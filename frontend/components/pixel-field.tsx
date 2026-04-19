"use client";

import { useEffect, useRef } from "react";


type Particle = {
  x: number;
  y: number;
  originX: number;
  originY: number;
  size: number;
  alpha: number;
  drift: number;
  phase: number;
  tint: "base" | "accent" | "soft";
};

const CLUSTER_COUNT = 380;
const FIELD_COUNT = 210;
const INTERACTION_RADIUS = 180;


export function PixelField() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }
    const drawingContext = context;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const pointer = {
      x: window.innerWidth * 0.5,
      y: window.innerHeight * 0.5,
      active: false,
    };
    let animationFrame = 0;
    let particles: Particle[] = [];

    function createParticles(width: number, height: number) {
      const clusterCenterX = width * 0.34;
      const clusterCenterY = height * 0.44;

      const clustered = Array.from({ length: CLUSTER_COUNT }, (_, index) => {
        const angle = Math.random() * Math.PI * 2;
        const radius = Math.pow(Math.random(), 0.72) * Math.min(width, height) * 0.18;
        return makeParticle({
          x: clusterCenterX + Math.cos(angle) * radius,
          y: clusterCenterY + Math.sin(angle) * radius,
          tint:
            index % 19 === 0 ? "accent" : index % 5 === 0 ? "soft" : "base",
          clustered: true,
        });
      });

      const field = Array.from({ length: FIELD_COUNT }, (_, index) =>
        makeParticle({
          x: Math.random() * width,
          y: Math.random() * height,
          tint: index % 11 === 0 ? "soft" : "base",
          clustered: false,
        }),
      );

      particles = [...field, ...clustered];
    }

    function makeParticle({
      x,
      y,
      tint,
      clustered,
    }: {
      x: number;
      y: number;
      tint: Particle["tint"];
      clustered: boolean;
    }): Particle {
      return {
        x,
        y,
        originX: x,
        originY: y,
        size: clustered ? 1.6 + Math.random() * 2.2 : 1 + Math.random() * 1.6,
        alpha: clustered ? 0.42 + Math.random() * 0.42 : 0.12 + Math.random() * 0.22,
        drift: 0.18 + Math.random() * 0.6,
        phase: Math.random() * Math.PI * 2,
        tint,
      };
    }

    function resizeCanvas() {
      const targetCanvas = canvasRef.current;
      if (!targetCanvas) {
        return;
      }
      const width = window.innerWidth;
      const height = window.innerHeight;
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      targetCanvas.width = width * ratio;
      targetCanvas.height = height * ratio;
      targetCanvas.style.width = `${width}px`;
      targetCanvas.style.height = `${height}px`;
      drawingContext.setTransform(ratio, 0, 0, ratio, 0, 0);
      createParticles(width, height);
    }

    function render(time: number) {
      const width = window.innerWidth;
      const height = window.innerHeight;
      drawingContext.clearRect(0, 0, width, height);

      for (const particle of particles) {
        const waveX = Math.cos(time * 0.00022 * particle.drift + particle.phase) * 8;
        const waveY = Math.sin(time * 0.00018 * particle.drift + particle.phase) * 8;

        let drawX = particle.originX + waveX;
        let drawY = particle.originY + waveY;

        if (!prefersReducedMotion && pointer.active) {
          const dx = drawX - pointer.x;
          const dy = drawY - pointer.y;
          const distance = Math.hypot(dx, dy);
          if (distance < INTERACTION_RADIUS) {
            const force = (1 - distance / INTERACTION_RADIUS) ** 1.8;
            drawX += (dx / Math.max(distance, 1)) * force * 34;
            drawY += (dy / Math.max(distance, 1)) * force * 34;
          }
        }

        const color = getColor(particle.tint, particle.alpha);
        drawingContext.fillStyle = color;
        drawingContext.fillRect(drawX, drawY, particle.size, particle.size);
      }

      animationFrame = window.requestAnimationFrame(render);
    }

    function handlePointerMove(event: PointerEvent) {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointer.active = true;
    }

    function handlePointerLeave() {
      pointer.active = false;
    }

    resizeCanvas();
    animationFrame = window.requestAnimationFrame(render);
    window.addEventListener("resize", resizeCanvas);
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerleave", handlePointerLeave);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", resizeCanvas);
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerleave", handlePointerLeave);
    };
  }, []);

  return (
    <div className="pixel-field" aria-hidden="true">
      <canvas ref={canvasRef} />
    </div>
  );
}


function getColor(tint: Particle["tint"], alpha: number) {
  if (tint === "accent") {
    return `rgba(143, 228, 211, ${alpha})`;
  }
  if (tint === "soft") {
    return `rgba(126, 167, 255, ${alpha * 0.72})`;
  }
  return `rgba(236, 242, 247, ${alpha})`;
}
