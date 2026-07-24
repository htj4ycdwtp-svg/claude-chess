const PIECE_SYMBOLS = {
  white: { pawn: "♙", knight: "♘", bishop: "♗", rook: "♖", queen: "♕", king: "♔" },
  black: { pawn: "♟", knight: "♞", bishop: "♝", rook: "♜", queen: "♛", king: "♚" },
};

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];
const RANKS = [8, 7, 6, 5, 4, 3, 2, 1];

const REASON_MESSAGES = {
  not_your_turn: "It's not your turn.",
  not_your_piece: "You can only move your own pieces.",
  illegal_move: "That move isn't legal.",
  invalid_square: "Invalid move.",
  not_in_game: "You're not currently in a game.",
  game_over: "The game is already over.",
  no_piece: "There's no piece on that square.",
};

let myColor = null;
let boardBuilt = false;
let lastBoardState = {};
let currentTurn = "white";
let selectedSquare = null;
let legalTargets = [];

const socket = io();

const lobbyEl = document.getElementById("lobby");
const gameEl = document.getElementById("game");
const lobbyMessageEl = document.getElementById("lobby-message");
const gameMessageEl = document.getElementById("game-message");
const statusEl = document.getElementById("status-display");
const gameCodeEl = document.getElementById("game-code-display");
const opponentEl = document.getElementById("opponent-display");
const boardEl = document.getElementById("board");

function buildBoard(orientation) {
  boardEl.innerHTML = "";
  const files = orientation === "black" ? [...FILES].reverse() : FILES;
  const ranks = orientation === "black" ? [...RANKS].reverse() : RANKS;

  for (const rank of ranks) {
    for (const file of files) {
      const square = file + rank;
      const fileIndex = FILES.indexOf(file);
      const isLight = (fileIndex + rank) % 2 === 0;
      const squareEl = document.createElement("div");
      squareEl.className = "square " + (isLight ? "light" : "dark");
      squareEl.dataset.square = square;
      squareEl.addEventListener("click", () => onSquareClick(square));
      boardEl.appendChild(squareEl);
    }
  }
}

function renderPieces(boardState) {
  document.querySelectorAll(".square").forEach((el) => {
    el.textContent = "";
    el.classList.remove("piece-white", "piece-black", "selected", "legal-target");
  });
  for (const [square, piece] of Object.entries(boardState)) {
    const el = boardEl.querySelector(`.square[data-square="${square}"]`);
    if (el) {
      el.textContent = PIECE_SYMBOLS[piece.color][piece.type];
      el.classList.add("piece-" + piece.color);
    }
  }
}

function highlightSelection() {
  document.querySelectorAll(".square").forEach((el) => {
    el.classList.remove("selected", "legal-target");
  });
  if (selectedSquare) {
    const el = boardEl.querySelector(`.square[data-square="${selectedSquare}"]`);
    if (el) el.classList.add("selected");
  }
  for (const square of legalTargets) {
    const el = boardEl.querySelector(`.square[data-square="${square}"]`);
    if (el) el.classList.add("legal-target");
  }
}

function clearSelection() {
  selectedSquare = null;
  legalTargets = [];
  highlightSelection();
}

function onSquareClick(square) {
  if (!myColor || currentTurn !== myColor) return;

  if (selectedSquare && legalTargets.includes(square)) {
    attemptMove(selectedSquare, square);
    clearSelection();
    return;
  }

  if (selectedSquare === square) {
    clearSelection();
    return;
  }

  const piece = lastBoardState[square];
  if (piece && piece.color === myColor) {
    selectedSquare = square;
    socket.emit("get_legal_moves", { square }, (response) => {
      legalTargets = (response && response.destinations) || [];
      highlightSelection();
    });
  } else {
    clearSelection();
  }
}

function attemptMove(from, to) {
  const piece = lastBoardState[from];
  let promotion = null;
  if (piece && piece.type === "pawn" && (to.endsWith("8") || to.endsWith("1"))) {
    promotion = promptForPromotion();
  }
  gameMessageEl.textContent = "";
  socket.emit("make_move", { from, to, promotion });
}

function promptForPromotion() {
  const choice = window.prompt("Promote to queen, rook, bishop, or knight?", "queen");
  const normalized = (choice || "queen").trim().toLowerCase();
  return ["queen", "rook", "bishop", "knight"].includes(normalized) ? normalized : "queen";
}

function updateStatusDisplay(payload) {
  if (payload.status === "checkmate") {
    statusEl.textContent = `Checkmate — ${payload.winner} wins`;
  } else if (payload.status === "stalemate") {
    statusEl.textContent = "Stalemate — draw";
  } else {
    const whoseTurn = payload.turn === myColor ? "Your move" : "Opponent's move";
    const checkNote = payload.status === "check" ? " (check!)" : "";
    statusEl.textContent = `${whoseTurn}${checkNote}`;
  }
}

function showGameScreen() {
  lobbyEl.classList.add("hidden");
  gameEl.classList.remove("hidden");
}

function updateOpponentDisplay(connected) {
  opponentEl.textContent = connected ? "Opponent connected" : "Waiting for opponent...";
}

function reconnectSocket() {
  if (socket.connected) {
    socket.disconnect();
  }
  socket.connect();
}

document.getElementById("create-btn").addEventListener("click", async () => {
  try {
    const res = await fetch("/api/create", { method: "POST" });
    if (!res.ok) throw new Error("create failed");
    reconnectSocket();
  } catch (err) {
    lobbyMessageEl.textContent = "Could not create a game. Please try again.";
  }
});

document.getElementById("join-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const codeInput = document.getElementById("join-code");
  const code = codeInput.value.trim().toUpperCase();
  if (!code) return;

  try {
    const res = await fetch("/api/join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_code: code }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      lobbyMessageEl.textContent =
        data.error === "not_found"
          ? "Game code not found."
          : data.error === "full"
          ? "That game already has two players."
          : "Could not join that game.";
      return;
    }
    reconnectSocket();
  } catch (err) {
    lobbyMessageEl.textContent = "Could not join a game. Please try again.";
  }
});

document.getElementById("restart-btn").addEventListener("click", () => {
  socket.emit("restart_game");
});

socket.on("state_update", (payload) => {
  lastBoardState = payload.board;
  currentTurn = payload.turn;

  if (payload.your_color && (payload.your_color !== myColor || !boardBuilt)) {
    myColor = payload.your_color;
    buildBoard(myColor);
    boardBuilt = true;
  }

  if (payload.game_code) {
    gameCodeEl.textContent = `Game code: ${payload.game_code}`;
  }
  if ("opponent_connected" in payload) {
    updateOpponentDisplay(payload.opponent_connected);
  }

  showGameScreen();
  renderPieces(lastBoardState);
  updateStatusDisplay(payload);
  clearSelection();
});

socket.on("opponent_status", (data) => {
  updateOpponentDisplay(data.connected);
});

socket.on("move_rejected", (data) => {
  gameMessageEl.textContent = REASON_MESSAGES[data.reason] || "Move rejected.";
});
