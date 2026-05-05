# Súper Cuadrito — Paquete Pygbag listo

## Estructura

```
super_cuadrito_pygbag/
├── main.py                    ← código principal con async + táctil
├── manifest.json              ← config de la PWA
├── sw.js                      ← service worker (offline)
├── index.html                 ← placeholder (pygbag lo reemplaza)
├── icon-32.png                ← favicon
├── icon-180.png               ← Apple touch
├── icon-192.png               ← Android pequeño
├── icon-512.png               ← Android grande
└── icon-512-maskable.png      ← Android adaptable
```

## Compilar

```bash
pip install pygbag
pygbag --build super_cuadrito_pygbag
```

Genera `super_cuadrito_pygbag/build/web/` listo para subir a itch.io o GitHub Pages.

## Probar local

```bash
pygbag super_cuadrito_pygbag
```

Abre http://localhost:8000

## Cambios aplicados al .py

1. ✅ `import asyncio`
2. ✅ Bucle envuelto en `async def main()` + `await asyncio.sleep(0)`
3. ✅ `time.sleep()` reemplazado por cooldown con `time.time()` (no bloquea)
4. ✅ Música arranca al primer toque (requisito navegador)
5. ✅ Eventos `FINGERDOWN/UP/MOTION` para multi-touch
6. ✅ Botones táctiles dibujados sobre el juego: D-pad + DISP/MURO/RAYO/ESC + PAUSA
7. ✅ Movimiento continuo desde toques (igual que teclas mantenidas)

## Controles táctiles J1

- **D-pad izquierda** → mover/saltar/agachar
- **🔫 DISP** → disparar (mantener pulsado)
- **MURO** → poner muro
- **RAYO** → rayo láser (mantener)
- **ESC** → escudo (mantener)
- **❚❚** (arriba-derecha) → pausa

J2 sigue con teclado en escritorio. Para 2 jugadores en móvil, se podría
añadir un set de botones espejado en la otra mitad de la pantalla.
