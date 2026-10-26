// 页面只做三件事：收集问题、发送 HTTP 请求、把返回的文字显示出来。

const messagesEl = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const newChatButton = document.querySelector("#new-chat");

let isSending = false;

// 每个浏览器标签页保存一个会话 ID，后端用它区分对话历史。
function loadSessionId() {
    let id = localStorage.getItem("chat_session_id");
    if (!id) {
        id = "web-" + Date.now() + "-" + Math.random().toString(16).slice(2);
        localStorage.setItem("chat_session_id", id);
    }
    return id;
}

let sessionId = loadSessionId();

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addMessage(role, text = "") {
    const article = document.createElement("article");
    article.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "我" : "AI";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    if (role === "user") {
        article.append(bubble, avatar);
    } else {
        article.append(avatar, bubble);
    }

    messagesEl.appendChild(article);
    scrollToBottom();
    return bubble;
}

function showWelcome() {
    addMessage(
        "assistant",
        "你好，我是智能家居售后助手。你可以咨询扫地机器人、空气净化器或智能门锁的使用、保养、故障和售后政策。"
    );
}

function showTyping(bubble) {
    bubble.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
}

function escapeHtml(text) {
    return text
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderInline(text) {
    return text
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

// 只处理最常用的 Markdown：标题、列表、加粗、斜体和行内代码。
// 先转义 HTML，因此模型返回的内容不会变成可执行的标签。
function renderMarkdown(source) {
    const lines = escapeHtml(source).split("\n");
    const html = [];
    let paragraph = [];
    let listType = null;

    function flushParagraph() {
        if (paragraph.length) {
            html.push(`<p>${paragraph.join("<br>")}</p>`);
            paragraph = [];
        }
    }

    function closeList() {
        if (listType) {
            html.push(`</${listType}>`);
            listType = null;
        }
    }

    for (const rawLine of lines) {
        const line = rawLine.trimEnd();

        if (!line.trim()) {
            flushParagraph();
            closeList();
            continue;
        }

        const heading = line.match(/^(#{1,4})\s+(.*)$/);
        if (heading) {
            flushParagraph();
            closeList();
            const level = Math.min(heading[1].length, 4);
            html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
            continue;
        }

        const unordered = line.match(/^\s*[-*+]\s+(.*)$/);
        const ordered = line.match(/^\s*\d+[.)]\s+(.*)$/);
        if (unordered || ordered) {
            flushParagraph();
            const nextType = unordered ? "ul" : "ol";
            if (listType !== nextType) {
                closeList();
                html.push(`<${nextType}>`);
                listType = nextType;
            }
            html.push(`<li>${renderInline((unordered || ordered)[1])}</li>`);
            continue;
        }

        closeList();
        paragraph.push(renderInline(line));
    }

    flushParagraph();
    closeList();
    return html.join("");
}

function setBusy(busy) {
    isSending = busy;
    input.disabled = busy;
    sendButton.disabled = busy;
    newChatButton.disabled = busy;
    sendButton.textContent = busy ? "回答中…" : "发送";
}

//前后端交互核心
async function sendMessage(text) {
    if (!text || isSending) {
        return;
    }

    setBusy(true);
    addMessage("user", text);
    input.value = "";
    input.style.height = "auto";

    const bubble = addMessage("assistant");
    showTyping(bubble);
    /*
    await = "在这儿停一下，等这个异步操作有结果（或出错）了再继续"。
    它只能用在 async 函数里，拿到的是 Promise resolve 的值，
    遇到 reject 会抛异常（可用 try/catch 接住），并且只暂停当前函数，不阻塞整个程序。
    */
    try {
        const response = await fetch("/api/chat", {  //会向当前网站的同名地址发请求
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                session_id: sessionId,
            }),
        });

        if (!response.ok) {
            const detail = await response.text();
            throw new Error(`HTTP ${response.status}：${detail}`);
        }

        if (!response.body) {
            throw new Error("当前浏览器不支持流式响应");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let answer = "";
        let firstChunk = true;

        while (true) {
            const { value, done } = await reader.read();
            if (done) {
                break;
            }

            if (firstChunk) {
                bubble.textContent = "";
                firstChunk = false;
            }

            // stream: true 可以正确处理被拆到两个网络包里的中文。
            answer += decoder.decode(value, { stream: true });
            bubble.innerHTML = renderMarkdown(answer);
            scrollToBottom();
        }

        answer += decoder.decode();
        if (answer.trim()) {
            bubble.innerHTML = renderMarkdown(answer);
        } else {
            bubble.textContent = "（智能体没有返回内容）";
        }
    } catch (error) {
        bubble.classList.add("error");
        bubble.textContent = "请求失败：" + error.message;
    } finally {
        setBusy(false);
        input.focus();
        scrollToBottom();
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(input.value.trim());
});

input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
    }
});

input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 160) + "px";
});

newChatButton.addEventListener("click", () => {
    if (isSending) {
        return;
    }

    sessionId = "web-" + Date.now() + "-" + Math.random().toString(16).slice(2);
    localStorage.setItem("chat_session_id", sessionId);
    messagesEl.replaceChildren();
    showWelcome();
    input.focus();
});

showWelcome();
