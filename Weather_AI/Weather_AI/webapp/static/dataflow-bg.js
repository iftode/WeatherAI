const canvas = document.getElementById("dataFlowCanvas");
const ctx = canvas.getContext("2d");

let w = 0;
let h = 0;

let particles = [];
let twinkles = [];
let pulse = 0;

function resizeCanvas() {
    const dpr = window.devicePixelRatio || 1;
    w = window.innerWidth;
    h = window.innerHeight;

    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    createScene();
}

class Particle {
    constructor() {
        this.reset();
    }

    reset() {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.radius = Math.random() * 1.6 + 0.3;
        this.speedX = Math.random() * 0.18 + 0.03;
        this.alpha = Math.random() * 0.25 + 0.05;
        this.color = this.randomColor();
    }

    randomColor() {
        const colors = [
            "44,230,255",
            "255,78,189",
            "255,213,94",
            "120,190,255"
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    update() {
        this.x += this.speedX;
        if (this.x > w + 10) {
            this.x = -10;
            this.y = Math.random() * h;
        }
    }

    draw() {
        ctx.beginPath();
        ctx.fillStyle = `rgba(${this.color}, ${this.alpha})`;
        ctx.shadowBlur = 10;
        ctx.shadowColor = `rgba(${this.color}, 0.7)`;
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
    }
}

class Twinkle {
    constructor() {
        this.reset();
    }

    reset() {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.size = Math.random() * 2 + 1;
        this.phase = Math.random() * Math.PI * 2;
        this.speed = Math.random() * 0.02 + 0.005;
        this.alpha = Math.random() * 0.2 + 0.05;
    }

    update() {
        this.phase += this.speed;
    }

    draw() {
        const a = this.alpha + Math.sin(this.phase) * 0.06;
        ctx.beginPath();
        ctx.fillStyle = `rgba(255,255,255,${Math.max(0, a)})`;
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

function createScene() {
    particles = [];
    twinkles = [];

    for (let i = 0; i < 90; i++) {
        particles.push(new Particle());
    }

    for (let i = 0; i < 45; i++) {
        twinkles.push(new Twinkle());
    }
}

function drawCoreGlow(time) {
    const x = w * 0.47;
    const y = h * 0.50;
    const r = 140 + Math.sin(time * 0.0016) * 8;

    const grad = ctx.createRadialGradient(x, y, 10, x, y, r);
    grad.addColorStop(0, "rgba(255,255,255,0.24)");
    grad.addColorStop(0.15, "rgba(44,230,255,0.16)");
    grad.addColorStop(0.35, "rgba(255,78,189,0.10)");
    grad.addColorStop(0.55, "rgba(255,213,94,0.05)");
    grad.addColorStop(1, "rgba(255,255,255,0)");

    ctx.beginPath();
    ctx.fillStyle = grad;
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
}

function drawInputGlow(time) {
    const lines = [
        { y: h * 0.318, color: "rgba(44,230,255,0.18)" },
        { y: h * 0.502, color: "rgba(255,78,189,0.16)" },
        { y: h * 0.688, color: "rgba(255,213,94,0.18)" }
    ];

    lines.forEach((line, index) => {
        ctx.beginPath();
        ctx.moveTo(0, line.y);

        for (let x = 0; x < w * 0.24; x += 8) {
            const wave = Math.sin((x * 0.014) + time * 0.002 + index) * 2;
            ctx.lineTo(x, line.y + wave);
        }

        ctx.strokeStyle = line.color;
        ctx.lineWidth = 4;
        ctx.shadowBlur = 22;
        ctx.shadowColor = line.color;
        ctx.stroke();
        ctx.shadowBlur = 0;
    });
}

function drawBinaryPulse(time) {
    const startX = w * 0.50;
    const endX = w * 0.92;
    const startY = h * 0.14;
    const endY = h * 0.86;

    const cols = 16;
    const rows = 10;

    const colGap = (endX - startX) / cols;
    const rowGap = (endY - startY) / rows;

    for (let c = 0; c < cols; c++) {
        for (let r = 0; r < rows; r++) {
            const x = startX + c * colGap + Math.sin((time * 0.0015) + c) * 1.2;
            const y = startY + r * rowGap + Math.cos((time * 0.0013) + r) * 1.2;

            const glow = 0.04 + (Math.sin(time * 0.002 + c * 0.8 + r * 0.5) + 1) * 0.018;

            let color = `rgba(44,230,255,${glow})`;
            if ((c + r) % 5 === 0) color = `rgba(255,78,189,${glow * 1.1})`;
            if ((c + r) % 7 === 0) color = `rgba(255,213,94,${glow * 1.1})`;

            ctx.beginPath();
            ctx.fillStyle = color;
            ctx.arc(x, y, 2.2, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

function animate(time) {
    ctx.clearRect(0, 0, w, h);

    drawCoreGlow(time);
    drawInputGlow(time);
    drawBinaryPulse(time);

    twinkles.forEach(t => {
        t.update();
        t.draw();
    });

    particles.forEach(p => {
        p.update();
        p.draw();
    });

    requestAnimationFrame(animate);
}

window.addEventListener("resize", resizeCanvas);

resizeCanvas();
requestAnimationFrame(animate);