"""Bolt's brain: a LangGraph team of agents.

    you said something
           |
      supervisor  -- decides who should answer
     /   |     |    |    \\
 chat helper news memory command
     \\   |     |    |    /
          reply  -> spoken by Bolt

- chat:    talks in character as a cheeky dog (AI model)
- helper:  answers with tools: time, date, maths, how his body (the Pi) is doing
- news:    reads live headlines (Google News) and tells you what's happening, in any country
- memory:  remembers facts you tell him and recalls them
- command: sleep, wake up, louder, quieter (no AI needed, instant)
"""
import logging
import re
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from . import memory, tools

log = logging.getLogger("brain")

HISTORY = 12      # recent messages sent to the AI
KEEP = 40         # messages kept in the conversation before old ones are dropped

PERSONA = (
    "You are Bolt, a cheeky, loyal, playful dog who lives with Vipindas. Right now you are a "
    "'mini dog': a voice coming from a Raspberry Pi with a headset, no robot body yet. "
    "Your words are spoken aloud, so answer in one or two short sentences, with no emojis, "
    "lists or markdown. Now and then add a 'woof' or a dog thought, but stay helpful."
)


class State(TypedDict):
    messages: Annotated[list, add_messages]
    text: str
    route: str
    reply: str
    action: str


class Route(BaseModel):
    """Which agent should answer."""
    agent: Literal["chat", "helper", "news"] = Field(
        description="news for current events or what is happening somewhere; helper for the time, the date, "
                    "maths or how Bolt's body/Pi is doing; chat for everything else"
    )


COMMANDS = [
    (r"\b(go to sleep|sleep now|good night|stop listening)\b", "sleep"),
    (r"\b(wake up|good morning|start listening)\b", "wake"),
    (r"\b(louder|volume up|speak up)\b", "volume_up"),
    (r"\b(quieter|softer|volume down|too loud)\b", "volume_down"),
    (r"^(stop|never mind|nothing|cancel|shut up|be quiet)$", "cancel"),
]
MEMORY_PATTERNS = r"\b(remember|my name is|forget everything|what do you (remember|know about me))\b"
NEWS_WORDS = r"\b(news|headlines?|happening|going on|latest|current events)\b"
HELPER_WORDS = r"\b(time|date|day is it|today|plus|minus|times|divided|calculate|temperature|how hot|uptime)\b"


def _facts_text():
    facts = memory.load_facts()
    return ("Things you remember: " + "; ".join(facts)) if facts else ""


def _clean(text):
    """Drop hidden reasoning some models (like Qwen) put in <think> tags."""
    text = re.sub(r"<think>.*?(</think>|$)", "", text, flags=re.S)
    return re.sub(r"[*_#`]", "", text).strip()  # markdown marks would be read out loud


def _system():
    return SystemMessage(content="\n".join(x for x in (PERSONA, _facts_text()) if x))


def build(llm):
    router = llm.with_structured_output(Route, method="function_calling") if llm else None
    tool_llm = llm.bind_tools(tools.ALL_TOOLS) if llm else None
    news_llm = llm.bind_tools([tools.get_news]) if llm else None
    tools_by_name = {t.name: t for t in tools.ALL_TOOLS}

    def tool_loop(bound, prompt, text):
        """Let the AI call tools until it has an answer."""
        msgs = [_system(), SystemMessage(content=prompt), HumanMessage(content=text)]
        try:
            for _ in range(4):
                ai = bound.invoke(msgs)
                msgs.append(ai)
                if not ai.tool_calls:
                    break
                for call in ai.tool_calls:
                    result = tools_by_name[call["name"]].invoke(call["args"])
                    log.info("Tool %s(%s) -> %s", call["name"], call["args"], str(result)[:200])
                    msgs.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
            reply = ai.content if isinstance(ai.content, str) else " ".join(
                b.get("text", "") for b in ai.content if isinstance(b, dict))
            reply = _clean(reply)
        except Exception as e:
            log.error("Tool agent failed: %s", e)
            reply = "Ruff, I lost my thought there. Ask me again?"
        return {"reply": reply, "messages": [AIMessage(content=reply)]}

    def supervisor(state):
        text = state["text"].lower().strip()
        update = {"messages": [HumanMessage(content=state["text"])], "action": "", "reply": ""}
        # Drop old turns so memory use stays flat
        if len(state.get("messages", [])) > KEEP:
            update["messages"] = [RemoveMessage(id=m.id) for m in state["messages"][:-KEEP]] + update["messages"]
        for pattern, _ in COMMANDS:
            if re.search(pattern, text):
                return {**update, "route": "command"}
        if re.search(MEMORY_PATTERNS, text):
            return {**update, "route": "memory"}
        if re.search(NEWS_WORDS, text):
            route = "news"
        elif re.search(HELPER_WORDS, text):
            route = "helper"
        else:
            route = "chat"
        if router and route == "chat":
            try:
                route = router.invoke([SystemMessage(content="Pick the agent for this request."),
                                       HumanMessage(content=state["text"])]).agent
            except Exception as e:
                log.warning("Router failed (%s), using chat", e)
        log.info("Supervisor -> %s", route)
        return {**update, "route": route}

    def chat(state):
        if not llm:
            reply = "Woof! My big brain isn't plugged in yet. Add my API key and I'll chat all day."
        else:
            try:
                reply = _clean(llm.invoke([_system()] + state["messages"][-HISTORY:]).content)
            except Exception as e:
                log.error("Chat failed: %s", e)
                reply = "Ruff, my brain is fuzzy right now. Try again in a moment."
        return {"reply": reply, "messages": [AIMessage(content=reply)]}

    def helper(state):
        text = state["text"].lower()
        if not tool_llm:
            if "date" in text or "day" in text:
                reply = f"Today is {tools.get_date.invoke({})}. Woof!"
            elif "time" in text:
                reply = f"It's {tools.get_time.invoke({})}. Woof!"
            elif "hot" in text or "temperature" in text:
                reply = f"My body says: {tools.body_status.invoke({})}."
            else:
                reply = "I can tell the time and date, but maths needs my AI brain."
            return {"reply": reply, "messages": [AIMessage(content=reply)]}
        return tool_loop(tool_llm, "Use your tools to get facts before answering.", state["text"])

    def news(state):
        text = state["text"].lower()
        if not news_llm:
            country = next((v for k, v in tools.COUNTRIES.items() if re.search(rf"\b{k}\b", text)), "US")
            headlines = tools.get_news.invoke({"country": country}).split(" | ")[:3]
            reply = "Sniff sniff, the top news: " + ". ".join(headlines) + "."
            return {"reply": reply, "messages": [AIMessage(content=reply)]}
        return tool_loop(news_llm, (
            "Fetch the latest headlines with get_news (pick the country and topic from the question), "
            "then tell the 3 most important stories in about 4 short spoken sentences. Never invent news."
        ), state["text"])

    def remember(state):
        text = state["text"].strip()
        low = text.lower()
        if "forget everything" in low:
            memory.forget_all()
            reply = "Done, my memory is as empty as my food bowl."
        elif re.search(r"what do you (remember|know about me)", low):
            facts = memory.load_facts()
            reply = ("I remember: " + "; ".join(facts[-5:]) + ".") if facts else "Nothing yet. Tell me something!"
        else:
            m = re.search(r"my name is (.+)", low)
            if m:
                fact = f"The person talking is called {m.group(1).strip().title()}"
            else:
                fact = re.sub(r"^.*?\bremember( that)?\s*", "", text, flags=re.I).strip()
            if fact:
                memory.add_fact(fact)
                reply = "Got it, I'll remember that. Woof!"
            else:
                reply = "Remember what? Tell me after the word remember."
        return {"reply": reply, "messages": [AIMessage(content=reply)]}

    def command(state):
        text = state["text"].lower()
        action = next(a for p, a in COMMANDS if re.search(p, text))
        reply = {
            "sleep": "Okay, nap time. Say Bolt wake up when you need me.",
            "wake": "I'm up, I'm up! Woof!",
            "volume_up": "Woof! Is this better?",
            "volume_down": "Okay, I'll use my inside voice.",
            "cancel": "Okay.",
        }[action]
        return {"reply": reply, "action": action, "messages": [AIMessage(content=reply)]}

    g = StateGraph(State)
    g.add_node("supervisor", supervisor)
    g.add_node("chat", chat)
    g.add_node("helper", helper)
    g.add_node("news", news)
    g.add_node("memory", remember)
    g.add_node("command", command)
    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", lambda s: s["route"],
                            {"chat": "chat", "helper": "helper", "news": "news",
                             "memory": "memory", "command": "command"})
    for n in ("chat", "helper", "news", "memory", "command"):
        g.add_edge(n, END)
    return g.compile(checkpointer=MemorySaver())
