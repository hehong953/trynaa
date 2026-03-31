let currentWord = "さしだす";
let currentPage = 1;

async function doSearch(page = 1) {
    const word = document.getElementById('searchBar').value.trim();
    if (!word) return;

    const res = await fetch(`/api/search?word=${encodeURIComponent(word)}&lang=ja&page=${page}`);
    const data = await res.json();

    const list = document.getElementById('resultList');
    list.innerHTML = data.results
        .map(r => `<li onclick="loadEntry('${r.id}')">${r.headword}</li>`)
        .join('');

    document.getElementById('pageInfo').innerText = `${data.current_page} / ${data.total_pages}`;
    document.getElementById('pagination').style.display = 'flex';
    currentPage = page;
}

document.getElementById('searchBar').addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        doSearch(1);
    }
});

document.getElementById('prevBtn').onclick = () => {
    if (currentPage > 1) doSearch(currentPage - 1);
};
document.getElementById('nextBtn').onclick = () => {
    doSearch(currentPage + 1);
};

async function loadEntry(id) {
    const res = await fetch(`/api/entry/ja/${id}`);
    document.getElementById('displayArea').innerHTML = await res.text();
}

let quizData = null;

async function loadNextQuiz() {
    document.getElementById('quizAnswerSection').style.display = 'none';

    const res = await fetch('/api/quiz/random');
    quizData = await res.json();

    const isKanaToKanji = Math.random() > 0.2;

    document.getElementById('quizType').innerText =
        isKanaToKanji ? "假名->漢字" : "漢字->假名";

    document.getElementById('quizCount').innerText =
        isKanaToKanji ? "有 " + quizData.count + " 個同音字" : "";

    document.getElementById('quizWord').innerText =
        isKanaToKanji ? quizData.kana : quizData.kanji;

    document.getElementById('quizResult').innerText =
        isKanaToKanji ? quizData.kanji : quizData.kana;

    if (quizData.count != 0) {
        document.getElementById('quizSameReading').innerText =
            "同音：" + quizData.kanjiList;
    } else {
        document.getElementById('quizSameReading').innerText = "";
    }

    document.getElementById('quizDetail').innerHTML = quizData.content;
}

function revealAnswer() {
    document.getElementById('quizAnswerSection').style.display = 'block';
}

window.onload = () => {
    loadNextQuiz();
};