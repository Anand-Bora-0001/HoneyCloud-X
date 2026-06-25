import React, { useEffect, useRef } from 'react';

const ParticlesBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const count = 10000;
    const posX = new Float32Array(count);
    const posY = new Float32Array(count);
    const velX = new Float32Array(count);
    const velY = new Float32Array(count);
    const size = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      posX[i] = Math.random() * width;
      posY[i] = Math.random() * height;
      velX[i] = (Math.random() - 0.5) * 0.3;
      velY[i] = (Math.random() - 0.5) * 0.3;
      size[i] = 0.5 + Math.random() * 1.0;
    }

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize, { passive: true });

    let animationFrameId;

    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.25)';
      ctx.beginPath();

      for (let i = 0; i < count; i++) {
        posX[i] += velX[i];
        posY[i] += velY[i];

        if (posX[i] < 0) posX[i] = width;
        else if (posX[i] > width) posX[i] = 0;

        if (posY[i] < 0) posY[i] = height;
        else if (posY[i] > height) posY[i] = 0;

        ctx.rect(posX[i], posY[i], size[i], size[i]);
      }

      ctx.fill();
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      id="honeycloud-particles"
      className="fixed inset-0 w-screen h-screen -z-[999] pointer-events-none"
    />
  );
};

export default ParticlesBackground;
