#!/usr/bin/env python3
# Súper Cuadrito V24 NORMALIZADA — versión Pygbag (web/Android)
# Adaptado para correr en navegador con controles táctiles
import asyncio
import pygame
import random
import time
import math
import os

# --- 1. CONFIGURACIÓN INICIAL ---
pygame.init()
try:
    pygame.mixer.init()
except Exception as _e:
    print(f"[audio] mixer.init falló: {_e}")

info_pantalla = pygame.display.Info()
W_FULL, H_FULL = info_pantalla.current_w, info_pantalla.current_h
ANCHO, ALTO = 800, 600
pantalla_completa = False

pantalla_real = pygame.display.set_mode((ANCHO, ALTO))
pantalla = pygame.Surface((ANCHO, ALTO))
pygame.display.set_caption("Súper Cuadrito: V24 NORMALIZADA")
reloj = pygame.time.Clock()

fuente_chica = pygame.font.SysFont("Arial", 16, bold=True)
fuente = pygame.font.SysFont("Arial", 22, bold=True)
fuente_grande = pygame.font.SysFont("Arial", 40, bold=True)
fuente_gigante = pygame.font.SysFont("Arial", 70, bold=True)

# Colores
BLANCO = (255, 255, 255); NEGRO = (0, 0, 0); GRIS = (150, 150, 150)
ROJO = (255, 50, 50); VERDE = (50, 200, 50); AZUL = (50, 150, 255)
AMARILLO = (255, 255, 0); MORADO = (150, 50, 250); CIAN = (0, 255, 255)

ARCOIRIS = [
    (255, 0, 0), (255, 127, 0), (255, 255, 0), (127, 255, 0),
    (0, 255, 0), (0, 255, 127), (0, 255, 255), (0, 127, 255),
    (0, 0, 255), (127, 0, 255), (255, 0, 255), (255, 0, 127),
    (0, 0, 0), (255, 255, 255), (150, 150, 150), (139, 69, 19)
]

volumen_musica = 0.5
brillo = 0
color_j1 = AZUL; color_j2 = ROJO
color_p1 = (139, 69, 19); color_p2 = GRIS
quien_cambia_color = ""

modo_dos_jugadores = False
pausado = False
esperando_tecla_para = None
musica_iniciada = False  # se carga al primer toque (los navegadores lo exigen)

controles = {
    'j1_arr': pygame.K_UP, 'j1_aba': pygame.K_DOWN, 'j1_izq': pygame.K_LEFT, 'j1_der': pygame.K_RIGHT,
    'j1_disp': pygame.K_SPACE, 'j1_rayo': pygame.K_b, 'j1_muro': pygame.K_n, 'j1_muros15': pygame.K_m,
    'j1_escudo': pygame.K_c, 'j1_bot': pygame.K_v,
    'j2_arr': pygame.K_w, 'j2_aba': pygame.K_s, 'j2_izq': pygame.K_a, 'j2_der': pygame.K_d,
    'j2_disp': pygame.K_f, 'j2_rayo': pygame.K_h, 'j2_muro': pygame.K_g, 'j2_muros15': pygame.K_6,
    'j2_escudo': pygame.K_e, 'j2_bot': pygame.K_q,
    'j2_hacker_dragon': pygame.K_1, 'j2_hacker_asalto': pygame.K_2, 'j2_hacker_dios': pygame.K_3,
    'sys_pausa': pygame.K_p, 'sys_congelar': pygame.K_x, 'sys_descongelar': pygame.K_z
}

# --- CONTROLES TÁCTILES ---
# Estado de cada botón táctil (True mientras un dedo lo está tocando)
tactil = {
    'izq': False, 'der': False, 'arr': False, 'aba': False,
    'disp': False, 'rayo': False, 'muro': False, 'escudo': False,
    'pausa': False,
}
# Mapa de qué dedo (finger_id) está sobre qué botón, para soltar bien
dedos_sobre = {}

# Definición de botones táctiles (rectángulos)
BTAM = 70  # tamaño botón
def rects_tactil():
    margen = 16
    # D-pad izquierda
    cx = margen + BTAM
    cy = ALTO - margen - BTAM
    rects = {
        'izq':    pygame.Rect(margen, cy - BTAM // 2, BTAM, BTAM),
        'der':    pygame.Rect(margen + BTAM * 2, cy - BTAM // 2, BTAM, BTAM),
        'arr':    pygame.Rect(margen + BTAM, cy - BTAM - BTAM // 2, BTAM, BTAM),
        'aba':    pygame.Rect(margen + BTAM, cy + BTAM // 2, BTAM, BTAM),
    }
    # Botones de acción derecha
    rx = ANCHO - margen
    ry = ALTO - margen - BTAM
    rects['disp']   = pygame.Rect(rx - BTAM, ry, BTAM, BTAM)
    rects['rayo']   = pygame.Rect(rx - BTAM * 2 - 8, ry, BTAM, BTAM)
    rects['muro']   = pygame.Rect(rx - BTAM, ry - BTAM - 8, BTAM, BTAM)
    rects['escudo'] = pygame.Rect(rx - BTAM * 2 - 8, ry - BTAM - 8, BTAM, BTAM)
    rects['pausa']  = pygame.Rect(ANCHO - 56 - 8, 8, 56, 40)
    return rects

BOTONES_RECTS = rects_tactil()

# Eventos one-shot generados desde toques (para acciones tipo "saltar" o "muro")
toques_pendientes = []
# Taps del frame actual (coords lógicas) — para que dibujar_boton funcione con dedo en menús
taps_frame = []

def coords_dedo(evento):
    """Convierte un evento FINGERDOWN/UP/MOTION a coords (x, y) del Surface lógico."""
    return (int(evento.x * ANCHO), int(evento.y * ALTO))

def coords_mouse(evento):
    return (evento.pos[0], evento.pos[1])

def detectar_boton(x, y):
    for nombre, rect in BOTONES_RECTS.items():
        if rect.collidepoint(x, y):
            return nombre
    return None

def dibujar_botones_tactil(superficie, modo='juego'):
    """Dibuja los controles táctiles. modo='juego' o 'menu'."""
    if modo != 'juego':
        return
    for nombre, rect in BOTONES_RECTS.items():
        pulsado = tactil.get(nombre, False)
        if nombre in ('izq', 'der', 'arr', 'aba'):
            color_fondo = (255, 255, 255, 60) if not pulsado else (0, 255, 255, 120)
            color_borde = BLANCO
            simbolos = {'izq': '◀', 'der': '▶', 'arr': '▲', 'aba': '▼'}
            simbolo = simbolos[nombre]
            color_simbolo = BLANCO
        else:
            colores_btn = {
                'disp': ROJO, 'rayo': AMARILLO, 'muro': GRIS, 'escudo': VERDE, 'pausa': AMARILLO,
            }
            color_fondo = colores_btn.get(nombre, BLANCO)
            color_borde = NEGRO
            etiquetas = {
                'disp': '🔫', 'rayo': 'RAYO', 'muro': 'MURO', 'escudo': 'ESC', 'pausa': '❚❚',
            }
            simbolo = etiquetas.get(nombre, nombre.upper())
            color_simbolo = NEGRO

        # capa translúcida
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        if isinstance(color_fondo, tuple) and len(color_fondo) == 4:
            s.fill(color_fondo)
        else:
            s.fill((*color_fondo, 220 if pulsado else 180))
        superficie.blit(s, rect.topleft)

        pygame.draw.rect(superficie, color_borde, rect, 3, border_radius=8)

        # texto/símbolo
        try:
            txt = fuente.render(simbolo, True, color_simbolo)
        except Exception:
            txt = fuente_chica.render(simbolo, True, color_simbolo)
        superficie.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

if False and os.path.exists("musica.ogg"):
    try:
        pygame.mixer.music.load("musica.ogg")
        pygame.mixer.music.set_volume(volumen_musica)
    except: pass

def pos_mouse():
    mx, my = pygame.mouse.get_pos()
    if pantalla_completa:
        return (int(mx / (W_FULL / ANCHO)), int(my / (H_FULL / ALTO)))
    return (mx, my)

def dibujar_boton(texto, x, y, ancho, alto, color_normal, color_hover, tam_fuente="grande"):
    mx, my = pos_mouse()
    click = pygame.mouse.get_pressed()
    rect = pygame.Rect(x, y, ancho, alto)
    color = color_hover if rect.collidepoint(mx, my) else color_normal

    pygame.draw.rect(pantalla, color, rect, border_radius=10)
    pygame.draw.rect(pantalla, NEGRO, rect, 3, border_radius=10)

    fnt = fuente_grande if tam_fuente == "grande" else fuente_chica
    txt_surf = fnt.render(texto, True, NEGRO)
    pantalla.blit(txt_surf, (x + ancho//2 - txt_surf.get_width()//2, y + alto//2 - txt_surf.get_height()//2))

    # Mouse (escritorio)
    if rect.collidepoint(mx, my) and click[0]:
        return True
    # Táctil (móvil): cualquier tap del frame que caiga dentro
    for tx, ty in taps_frame:
        if rect.collidepoint(tx, ty):
            return True
    return False

def iniciar_juego(dos_jugadores):
    global j1_x, j1_y, j1_vy, j1_saltos, j1_agachado, j1_vivo, modo_dragon, dragon_timer
    global j2_x, j2_y, j2_vy, j2_saltos, j2_agachado, j2_vivo
    global balas, enemigos, items_dragon, particulas, trampas_negras, items_escudo, items_pistola
    global balas_restantes, puntaje, estado_juego, recarga, vel_global, pausado
    global modo_escudo, escudo_timer, nivel, tiempo_penalizacion
    global modo_pistola, balas_pistola, modo_bot, dog1_x, dog1_y, dog2_x, dog2_y, temblor
    global ultimo_disparo_j1, ultimo_disparo_j2, muros, j2_modo_bot, j2_modo_pistola, j2_balas_pistola
    global j2_modo_dragon, j2_dragon_timer, j2_modo_escudo, j2_escudo_timer
    global tiempo_congelado, modo_dos_jugadores, jefes, jefes_generados
    global tiempo_consumo_c_j1, tiempo_consumo_c_j2

    modo_dos_jugadores = dos_jugadores
    estado_juego = "JUGANDO"
    tiempo_congelado = False
    pausado = False

    j1_x, j1_y = 50, ALTO - 140; j1_vy = 0; j1_saltos = 0; j1_agachado = False; j1_vivo = True
    modo_bot = False; modo_dragon = False; dragon_timer = 0
    modo_pistola = False; balas_pistola = 0; modo_escudo = False; escudo_timer = 0
    tiempo_consumo_c_j1 = 0

    j2_x, j2_y = 100, ALTO - 140; j2_vy = 0; j2_saltos = 0; j2_agachado = False; j2_vivo = dos_jugadores
    j2_modo_bot = False; j2_modo_dragon = False; j2_dragon_timer = 0
    j2_modo_pistola = False; j2_balas_pistola = 0; j2_modo_escudo = False; j2_escudo_timer = 0
    tiempo_consumo_c_j2 = 0

    nivel = 1; tiempo_penalizacion = time.time(); temblor = 0
    balas = []; enemigos = []; items_dragon = []; particulas = []; trampas_negras = []
    items_escudo = []; items_pistola = []; balas_restantes = 50; puntaje = 0
    recarga = 0; vel_global = 6; ultimo_disparo_j1 = 0; ultimo_disparo_j2 = 0
    dog1_x, dog1_y = 20, ALTO - 120; dog2_x, dog2_y = 130, ALTO - 120
    muros = []
    jefes = []; jefes_generados = False

estado_juego = "JUGANDO"
corriendo = True
gravedad = 0.8
piso_y = ALTO - 100
ultimo_click_menu = 0  # cooldown para menús (reemplaza time.sleep)
iniciar_juego(False)


async def main():
    global corriendo, estado_juego, pantalla_completa, pantalla_real
    global volumen_musica, color_j1, color_j2, quien_cambia_color
    global esperando_tecla_para, modo_dos_jugadores, pausado, ultimo_click_menu, musica_iniciada

    while corriendo:
        pantalla.fill(BLANCO)
        teclas = pygame.key.get_pressed()
        t_actual = time.time()

        # Limpiar one-shot tactiles del frame anterior
        toques_pendientes.clear()
        taps_frame.clear()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False

            # --- MUSICA: desactivada ---
            if not musica_iniciada and evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                musica_iniciada = True

            # --- TECLADO ---
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    if estado_juego == "JUGANDO":
                        pausado = not pausado
                    else:
                        corriendo = False

                if estado_juego == "CONTROLES" and esperando_tecla_para:
                    if evento.key != pygame.K_ESCAPE:
                        controles[esperando_tecla_para] = evento.key
                    esperando_tecla_para = None
                    continue

                if estado_juego in ["PERDISTE", "VICTORIA"] and evento.key == pygame.K_RETURN:
                    iniciar_juego(modo_dos_jugadores)

                if estado_juego == "JUGANDO":
                    if evento.key == controles['sys_pausa']:
                        pausado = not pausado
                    if not pausado:
                        if j1_vivo:
                            if evento.key == controles['sys_congelar']: tiempo_congelado = True
                            if evento.key == controles['sys_descongelar']: tiempo_congelado = False
                            if not modo_bot and evento.key == controles['j1_arr']:
                                if modo_dragon: j1_vy = -8
                                elif j1_saltos < 2: j1_vy = -14; j1_saltos += 1
                            if evento.key == controles['j1_bot']: modo_bot = not modo_bot
                        if j2_vivo:
                            if not j2_modo_bot and evento.key == controles['j2_arr']:
                                if j2_modo_dragon: j2_vy = -8
                                elif j2_saltos < 2: j2_vy = -14; j2_saltos += 1
                        if not tiempo_congelado:
                            if evento.key == controles['j1_muro'] and j1_vivo: muros.append(0)
                            if evento.key == controles['j1_muros15'] and j1_vivo:
                                muros.extend([-i * 150 for i in range(15)]); temblor = 30
                            if j2_vivo:
                                if evento.key == controles['j2_muro']: muros.append(0)
                                if evento.key == controles['j2_muros15']:
                                    muros.extend([-i * 150 for i in range(15)]); temblor = 30
                                if evento.key == controles['j2_hacker_dragon']: j2_modo_dragon = True; j2_dragon_timer = time.time() + 10
                                if evento.key == controles['j2_hacker_asalto']: j2_modo_pistola = True; j2_balas_pistola = 50
                                if evento.key == controles['j2_hacker_dios']: j2_modo_escudo = True; j2_escudo_timer = time.time() + 15
                                if evento.key == controles['j2_bot']: j2_modo_bot = not j2_modo_bot

            # --- TÁCTIL por zonas (sin botones visibles) ---
            # Mitad izquierda de pantalla = movimiento (izq/der según x), arriba=saltar, abajo=agachar
            # Mitad derecha = disparar (mantener)
            if evento.type == pygame.FINGERDOWN:
                x, y = coords_dedo(evento)
                taps_frame.append((x, y))
                if x < ANCHO // 2:
                    # Zona movimiento
                    if y < ALTO * 0.35:
                        # Tap arriba = saltar (one-shot)
                        if j1_vivo:
                            if modo_dragon:
                                j1_vy = -8
                            elif j1_saltos < 2:
                                j1_vy = -14; j1_saltos += 1
                        dedos_sobre[evento.finger_id] = 'arr_tap'
                    elif y > ALTO * 0.70:
                        tactil['aba'] = True
                        dedos_sobre[evento.finger_id] = 'aba'
                    else:
                        # Mitad media: izq o der según posición x dentro del lado izquierdo
                        if x < ANCHO * 0.25:
                            tactil['izq'] = True
                            dedos_sobre[evento.finger_id] = 'izq'
                        else:
                            tactil['der'] = True
                            dedos_sobre[evento.finger_id] = 'der'
                else:
                    # Zona disparo
                    tactil['disp'] = True
                    dedos_sobre[evento.finger_id] = 'disp'
            elif evento.type == pygame.FINGERUP:
                accion = dedos_sobre.pop(evento.finger_id, None)
                if accion in ('izq', 'der', 'aba', 'disp'):
                    tactil[accion] = False
            elif evento.type == pygame.FINGERMOTION:
                # Permitir deslizar entre izq/der sin levantar el dedo
                x, y = coords_dedo(evento)
                accion_prev = dedos_sobre.get(evento.finger_id)
                if accion_prev in ('izq', 'der'):
                    nueva = 'izq' if x < ANCHO * 0.25 else ('der' if x < ANCHO // 2 else None)
                    if nueva != accion_prev:
                        tactil[accion_prev] = False
                        if nueva:
                            tactil[nueva] = True
                            dedos_sobre[evento.finger_id] = nueva
                        else:
                            dedos_sobre.pop(evento.finger_id, None)

            # --- MOUSE: simular dedo en zonas ---
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                x, y = coords_mouse(evento)
                taps_frame.append((x, y))
                if x < ANCHO // 2:
                    if y < ALTO * 0.35:
                        if j1_vivo:
                            if modo_dragon:
                                j1_vy = -8
                            elif j1_saltos < 2:
                                j1_vy = -14; j1_saltos += 1
                        dedos_sobre['mouse'] = 'arr_tap'
                    elif y > ALTO * 0.70:
                        tactil['aba'] = True
                        dedos_sobre['mouse'] = 'aba'
                    else:
                        if x < ANCHO * 0.25:
                            tactil['izq'] = True
                            dedos_sobre['mouse'] = 'izq'
                        else:
                            tactil['der'] = True
                            dedos_sobre['mouse'] = 'der'
                else:
                    tactil['disp'] = True
                    dedos_sobre['mouse'] = 'disp'
            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                accion = dedos_sobre.pop('mouse', None)
                if accion in ('izq', 'der', 'aba', 'disp'):
                    tactil[accion] = False

        # --- Procesar one-shot del táctil ---
        for ev in toques_pendientes:
            if ev[0] == 'down':
                btn = ev[1]
                if btn == 'pausa' and estado_juego == "JUGANDO":
                    pausado = not pausado
                if estado_juego == "JUGANDO" and not pausado:
                    if btn == 'arr' and j1_vivo:
                        if modo_dragon:
                            j1_vy = -8
                        elif j1_saltos < 2:
                            j1_vy = -14; j1_saltos += 1
                    if btn == 'muro' and j1_vivo:
                        muros.append(0)

        # ─────────── MENÚ ───────────
        if estado_juego == "MENU":
            pantalla.fill((10, 10, 30))
            titulo = fuente_gigante.render("SÚPER CUADRITO", True, CIAN)
            pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 100))

            if t_actual - ultimo_click_menu > 0.25:
                if dibujar_boton("JUGAR", ANCHO//2 - 150, 250, 300, 60, VERDE, (100, 255, 100)):
                    iniciar_juego(False); ultimo_click_menu = t_actual
                if dibujar_boton("AJUSTES", ANCHO//2 - 150, 350, 300, 60, AMARILLO, (255, 255, 100)):
                    estado_juego = "AJUSTES"; ultimo_click_menu = t_actual
            else:
                dibujar_boton("JUGAR", ANCHO//2 - 150, 250, 300, 60, VERDE, (100, 255, 100))
                dibujar_boton("AJUSTES", ANCHO//2 - 150, 350, 300, 60, AMARILLO, (255, 255, 100))

        elif estado_juego == "SELECCION_JUGADORES":
            pantalla.fill((10, 30, 10))
            titulo = fuente_gigante.render("ELIGE MODO", True, BLANCO)
            pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 100))

            if t_actual - ultimo_click_menu > 0.25:
                if dibujar_boton("1 JUGADOR", ANCHO//2 - 150, 250, 300, 60, AZUL, (100, 200, 255)):
                    iniciar_juego(False); ultimo_click_menu = t_actual
                if dibujar_boton("2 JUGADORES", ANCHO//2 - 150, 350, 300, 60, ROJO, (255, 100, 100)):
                    iniciar_juego(True); ultimo_click_menu = t_actual
                if dibujar_boton("VOLVER", 20, 20, 150, 40, GRIS, BLANCO):
                    estado_juego = "MENU"; ultimo_click_menu = t_actual
            else:
                dibujar_boton("1 JUGADOR", ANCHO//2 - 150, 250, 300, 60, AZUL, (100, 200, 255))
                dibujar_boton("2 JUGADORES", ANCHO//2 - 150, 350, 300, 60, ROJO, (255, 100, 100))
                dibujar_boton("VOLVER", 20, 20, 150, 40, GRIS, BLANCO)

        elif estado_juego == "AJUSTES":
            pantalla.fill((30, 10, 10))
            if t_actual - ultimo_click_menu > 0.25:
                if dibujar_boton("VOLVER", 20, 20, 150, 40, GRIS, BLANCO):
                    estado_juego = "MENU"; ultimo_click_menu = t_actual
                if dibujar_boton("Elegir Color", ANCHO//2 - 170, 200, 340, 50, color_j1, BLANCO, "chica"):
                    estado_juego = "COLOR_PICKER"; quien_cambia_color = "J1"; ultimo_click_menu = t_actual
            else:
                dibujar_boton("VOLVER", 20, 20, 150, 40, GRIS, BLANCO)
                dibujar_boton("Elegir Color", ANCHO//2 - 170, 200, 340, 50, color_j1, BLANCO, "chica")

        elif estado_juego == "COLOR_PICKER":
            pantalla.fill(NEGRO)
            titulo = fuente_grande.render("ELIGE UN COLOR", True, BLANCO)
            pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 50))
            tam_cuadro = 80; margen = 20
            inicio_x = (ANCHO - (4 * tam_cuadro + 3 * margen)) // 2; inicio_y = 150
            mx, my = pos_mouse()
            click = pygame.mouse.get_pressed()
            for i, color in enumerate(ARCOIRIS):
                fila = i // 4; col = i % 4
                x = inicio_x + col * (tam_cuadro + margen)
                y = inicio_y + fila * (tam_cuadro + margen)
                rect_color = pygame.Rect(x, y, tam_cuadro, tam_cuadro)
                pygame.draw.rect(pantalla, color, rect_color, border_radius=10)
                if rect_color.collidepoint(mx, my):
                    pygame.draw.rect(pantalla, BLANCO, rect_color, 4, border_radius=10)
                    if click[0] and t_actual - ultimo_click_menu > 0.25:
                        if quien_cambia_color == "J1": color_j1 = color
                        elif quien_cambia_color == "J2": color_j2 = color
                        estado_juego = "AJUSTES"; ultimo_click_menu = t_actual
            if dibujar_boton("CANCELAR", ANCHO//2 - 100, ALTO - 80, 200, 50, GRIS, BLANCO):
                if t_actual - ultimo_click_menu > 0.25:
                    estado_juego = "AJUSTES"; ultimo_click_menu = t_actual

        elif estado_juego == "JUGANDO":
            if not pausado:
                # Movimiento continuo desde TÁCTIL (igual que teclas mantenidas)
                if j1_vivo and not modo_bot:
                    if tactil['izq'] or teclas[controles['j1_izq']]: j1_x -= 8
                    if tactil['der'] or teclas[controles['j1_der']]: j1_x += 8
                    if modo_dragon:
                        if tactil['arr'] or teclas[controles['j1_arr']]: j1_y -= 8
                        if tactil['aba'] or teclas[controles['j1_aba']]: j1_y += 8
                    j1_agachado = (tactil['aba'] or teclas[controles['j1_aba']]) and not modo_dragon

                escudo_c_j1_activo = False
                if j1_vivo and (tactil['escudo'] or teclas[controles['j1_escudo']]) and balas_restantes > 0 and not modo_bot:
                    escudo_c_j1_activo = True
                    if t_actual - tiempo_consumo_c_j1 > 0.15:
                        balas_restantes -= 1; tiempo_consumo_c_j1 = t_actual

                escudo_e_j2_activo = False
                if j2_vivo and teclas[controles['j2_escudo']] and balas_restantes > 0 and not j2_modo_bot:
                    escudo_e_j2_activo = True
                    if t_actual - tiempo_consumo_c_j2 > 0.15:
                        balas_restantes -= 1; tiempo_consumo_c_j2 = t_actual

                if puntaje >= 24950:
                    nivel = 500
                    if not jefes_generados:
                        jefes_generados = True
                        jefes = [
                            [ANCHO-150, 50, 100, 15, 2500, NEGRO],
                            [ANCHO-300, 250, 100, -18, 2500, (100, 0, 0)],
                            [ANCHO-100, ALTO-250, 100, 22, 2500, (80, 0, 80)]
                        ]
                        trampas_negras.clear(); enemigos.clear(); temblor = 40
                else:
                    nivel = min(499, (puntaje // 50) + 1)

                COLOR_FONDO = (30, 0, 0) if nivel >= 500 else (20, 40, 80)
                pantalla.fill(COLOR_FONDO)
                vel_global = 6 + (nivel * 0.1)

                if j1_x < 0: j1_x = 0
                if j1_x > ANCHO - 40: j1_x = ANCHO - 40
                if not j1_vivo: j1_x = -100
                j1_y_dib = j1_y + 20 if j1_agachado else j1_y

                if j2_vivo:
                    if not j2_modo_bot:
                        if teclas[controles['j2_izq']]: j2_x -= 8
                        if teclas[controles['j2_der']]: j2_x += 8
                        j2_agachado = teclas[controles['j2_aba']] and not j2_modo_dragon
                    if j2_x < 0: j2_x = 0
                    if j2_x > ANCHO - 40: j2_x = ANCHO - 40
                else:
                    j2_x = -100
                j2_y_dib = j2_y + 20 if j2_agachado else j2_y

                if j1_vivo:
                    if modo_dragon:
                        if modo_bot:
                            if j1_y > piso_y - 160: j1_y -= 5
                            elif j1_y < piso_y - 260: j1_y += 5
                        if time.time() > dragon_timer: modo_dragon = False
                    else:
                        j1_vy += gravedad; j1_y += j1_vy
                        if j1_y >= piso_y - 40: j1_y = piso_y - 40; j1_vy = 0; j1_saltos = 0

                if j2_vivo:
                    if j2_modo_dragon:
                        if j2_modo_bot:
                            if j2_y > piso_y - 160: j2_y -= 5
                            elif j2_y < piso_y - 260: j2_y += 5
                        else:
                            if teclas[controles['j2_arr']]: j2_y -= 8
                            if teclas[controles['j2_aba']]: j2_y += 8
                        if time.time() > j2_dragon_timer: j2_modo_dragon = False
                    else:
                        j2_vy += gravedad; j2_y += j2_vy
                        if j2_y >= piso_y - 40: j2_y = piso_y - 40; j2_vy = 0; j2_saltos = 0

                dog1_x += (j1_x - 30 - dog1_x) * 0.1; dog1_y += (j1_y_dib + 20 - dog1_y) * 0.1
                if j2_vivo:
                    dog2_x += (j2_x + 30 - dog2_x) * 0.1; dog2_y += (j2_y_dib + 20 - dog2_y) * 0.1
                else:
                    dog2_x = -100

                j1_ray = j1_vivo and (tactil['rayo'] or teclas[controles['j1_rayo']]) and not modo_bot and not tiempo_congelado
                j2_ray = j2_vivo and teclas[controles['j2_rayo']] and not j2_modo_bot and not tiempo_congelado

                if j1_vivo and not tiempo_congelado and not escudo_c_j1_activo:
                    if (tactil['disp'] or teclas[controles['j1_disp']]) or (modo_bot and (enemigos or len(jefes) > 0)):
                        if t_actual - ultimo_disparo_j1 > (0.03 if modo_pistola else (0.08 if modo_dragon else 0.15)) and not j1_ray:
                            if balas_restantes > 0 or modo_bot or modo_pistola:
                                balas.append([j1_x + 40, j1_y_dib + 10, modo_dragon, modo_pistola, False])
                                balas.append([dog1_x + 15, dog1_y, False, False, True])
                                if modo_pistola:
                                    balas_pistola -= 1
                                    if balas_pistola <= 0: modo_pistola = False
                                elif not modo_dragon and not modo_bot: balas_restantes -= 1
                                ultimo_disparo_j1 = t_actual

                if j2_vivo and not tiempo_congelado and not escudo_e_j2_activo:
                    if teclas[controles['j2_disp']] or (j2_modo_bot and (enemigos or len(jefes) > 0)):
                        if t_actual - ultimo_disparo_j2 > (0.03 if j2_modo_pistola else (0.08 if j2_modo_dragon else 0.15)) and not j2_ray:
                            if balas_restantes > 0 or j2_modo_bot or j2_modo_pistola:
                                balas.append([j2_x + 40, j2_y_dib + 10, j2_modo_dragon, j2_modo_pistola, False])
                                balas.append([dog2_x, dog2_y, False, False, True])
                                if j2_modo_pistola:
                                    j2_balas_pistola -= 1
                                    if j2_balas_pistola <= 0: j2_modo_pistola = False
                                elif not j2_modo_dragon and not j2_modo_bot: balas_restantes -= 1
                                ultimo_disparo_j2 = t_actual

                if not tiempo_congelado:
                    for i in range(len(muros)): muros[i] += 20
                    muros[:] = [m for m in muros if m < ANCHO]

                    if random.randint(1, 150) == 1: items_dragon.append(pygame.Rect(ANCHO, random.randint(piso_y-300, piso_y-100), 40, 20))
                    if random.randint(1, 200) == 1: items_escudo.append([ANCHO, random.randint(piso_y-250, piso_y-50)])
                    if random.randint(1, 250) == 1: items_pistola.append(pygame.Rect(ANCHO, random.randint(piso_y-250, piso_y-50), 30, 15))
                    if random.randint(1, 100) == 1: trampas_negras.append([ANCHO, random.randint(piso_y-250, piso_y-20)])
                    if random.randint(1, max(5, 50 - int(nivel*0.1))) == 1:
                        enemigos.append([ANCHO, piso_y-60, 60, 60, NEGRO, 5 + int(nivel*0.1), True])

                    for i in items_dragon: i.x -= vel_global
                    for i in items_pistola: i.x -= vel_global
                    for e in items_escudo: e[0] -= vel_global
                    for t in trampas_negras: t[0] -= vel_global

                    for jefe in jefes:
                        jefe[1] += jefe[3]
                        if jefe[1] < 50 or jefe[1] > piso_y - 150: jefe[3] *= -1
                        if random.randint(1, 100) == 1:
                            trampas_negras.append([jefe[0], jefe[1] + jefe[2]//2])

                    b_del = []; e_del = []; t_del = []
                    for b in balas:
                        b[0] += 25 if b[3] else 16
                        r_b = pygame.Rect(b[0], b[1], 20, 5)
                        for jefe in jefes:
                            if r_b.colliderect(pygame.Rect(jefe[0], jefe[1], jefe[2], jefe[2])):
                                b_del.append(b); jefe[4] -= 1
                        for en in enemigos:
                            if r_b.colliderect(pygame.Rect(en[0], en[1], en[2], en[3])):
                                b_del.append(b); en[5] -= 1
                                if en[5] <= 0:
                                    e_del.append(en); puntaje += 5
                        if b[0] > ANCHO: b_del.append(b)
                    for b in b_del:
                        if b in balas: balas.remove(b)

                    r_j1 = pygame.Rect(j1_x, j1_y_dib, 40, 20 if j1_agachado else 40)
                    r_j2 = pygame.Rect(j2_x, j2_y_dib, 40, 20 if j2_agachado else 40)

                    for t in trampas_negras:
                        r_t = pygame.Rect(t[0]-15, t[1]-15, 30, 30)
                        destruido = any(pygame.Rect(m, 0, 50, ALTO).colliderect(r_t) for m in muros) or \
                                    (j1_ray and pygame.Rect(j1_x, j1_y_dib, ANCHO, 30).colliderect(r_t))
                        if destruido: t_del.append(t); puntaje += 10; continue
                        if j1_vivo and not j1_agachado and r_j1.colliderect(r_t):
                            if modo_escudo or modo_bot or escudo_c_j1_activo: t_del.append(t); puntaje += 5
                            else: j1_vivo = False
                    for t in t_del:
                        if t in trampas_negras: trampas_negras.remove(t)

                    for en in enemigos:
                        en[0] -= vel_global
                        r_e = pygame.Rect(en[0], en[1], en[2], en[3])
                        destruido = any(pygame.Rect(m, 0, 50, ALTO).colliderect(r_e) for m in muros) or \
                                    (j1_ray and pygame.Rect(j1_x, j1_y_dib, ANCHO, 30).colliderect(r_e))
                        if destruido: e_del.append(en); puntaje += 5; continue
                        if j1_vivo and not j1_agachado and r_j1.colliderect(r_e):
                            if modo_escudo or modo_bot or escudo_c_j1_activo: e_del.append(en); puntaje += 5
                            else: j1_vivo = False
                    for e in e_del:
                        if e in enemigos: enemigos.remove(e)

                    for i in items_dragon[:]:
                        if j1_vivo and r_j1.colliderect(i): modo_dragon = True; dragon_timer = time.time()+10; items_dragon.remove(i)
                    for i in items_pistola[:]:
                        if j1_vivo and r_j1.colliderect(i): modo_pistola = True; balas_pistola = 50; items_pistola.remove(i)
                    for e in items_escudo[:]:
                        r_esc = pygame.Rect(e[0]-15, e[1], 30, 25)
                        if j1_vivo and r_j1.colliderect(r_esc): modo_escudo = True; escudo_timer = time.time()+15; items_escudo.remove(e)

                    if modo_escudo and time.time() > escudo_timer: modo_escudo = False
                    if j2_modo_escudo and time.time() > j2_escudo_timer: j2_modo_escudo = False

                    for jefe in jefes[:]:
                        r_boss = pygame.Rect(jefe[0], jefe[1], jefe[2], jefe[2])
                        if j1_ray and pygame.Rect(j1_x, j1_y_dib, ANCHO, 30).colliderect(r_boss): jefe[4] -= 0.5
                        if any(pygame.Rect(m, 0, 50, ALTO).colliderect(r_boss) for m in muros): jefe[4] -= 2
                        if jefe[4] <= 0: jefes.remove(jefe); temblor = 30

                    if nivel >= 500 and len(jefes) == 0 and jefes_generados:
                        estado_juego = "VICTORIA"; temblor = 50

                    if not j1_vivo and not j2_vivo:
                        estado_juego = "PERDISTE"

                    recarga += 1
                    if recarga >= 25 and balas_restantes < 50: balas_restantes += 1; recarga = 0

            # --- DIBUJAR JUEGO ---
            COLOR_FONDO = (30, 0, 0) if nivel >= 500 else (20, 40, 80)
            pantalla.fill(COLOR_FONDO)
            pygame.draw.rect(pantalla, (20, 100, 20), (0, piso_y, ANCHO, ALTO - piso_y))
            brillo_radio = 25 + math.sin(time.time() * 10) * 5
            for i in items_dragon: pygame.draw.circle(pantalla, (100, 0, 150), (i.x+20, i.y+10), brillo_radio)
            for i in items_pistola: pygame.draw.circle(pantalla, (80, 80, 80), (i.x+15, i.y+7), brillo_radio)
            for e in items_escudo: pygame.draw.circle(pantalla, (0, 150, 0), (e[0], e[1]+12), brillo_radio)
            for m in muros:
                pygame.draw.rect(pantalla, NEGRO, (m, 0, 50, ALTO))
                pygame.draw.rect(pantalla, GRIS, (m+10, 0, 30, ALTO))
            if j1_ray:
                pygame.draw.rect(pantalla, AMARILLO, (j1_x+40, j1_y_dib+5, ANCHO, 40)); temblor = 3
                pygame.draw.rect(pantalla, AMARILLO, (dog1_x+10, dog1_y+5, ANCHO, 10))
            for b in balas: pygame.draw.rect(pantalla, BLANCO if b[4] else (CIAN if b[3] else AMARILLO), (b[0], b[1], 10 if b[4] else 20, 3 if b[4] else 5))
            for en in enemigos:
                pygame.draw.rect(pantalla, en[4], (en[0], en[1], en[2], en[3]))
                if en[6]:
                    pygame.draw.rect(pantalla, ROJO, (en[0] + 10, en[1] + 15, 15, 10))
                    pygame.draw.rect(pantalla, ROJO, (en[0] + 35, en[1] + 15, 15, 10))
            for i in items_dragon: pygame.draw.rect(pantalla, MORADO, i)
            for i in items_pistola:
                pygame.draw.rect(pantalla, GRIS, i); pygame.draw.rect(pantalla, NEGRO, (i.x - 5, i.y + 5, 5, 10))
            for e in items_escudo: pygame.draw.polygon(pantalla, VERDE, [(e[0], e[1]), (e[0]-15, e[1]+25), (e[0]+15, e[1]+25)])
            for t in trampas_negras: pygame.draw.circle(pantalla, MORADO, (t[0], t[1]), 20); pygame.draw.circle(pantalla, NEGRO, (t[0], t[1]), 15)
            for jefe in jefes:
                pygame.draw.rect(pantalla, jefe[5], (jefe[0], jefe[1], jefe[2], jefe[2]))
                pygame.draw.rect(pantalla, ROJO, (jefe[0], jefe[1] - 15, jefe[2], 10))
                pygame.draw.rect(pantalla, VERDE, (jefe[0], jefe[1] - 15, max(0, jefe[4]) * (jefe[2]/2500), 10))
                pygame.draw.rect(pantalla, ROJO, (jefe[0]+20, jefe[1]+20, 20, 20))
                pygame.draw.rect(pantalla, ROJO, (jefe[0]+60, jefe[1]+20, 20, 20))
            if j1_vivo:
                pygame.draw.rect(pantalla, color_j1, (j1_x, j1_y_dib, 40, 20 if j1_agachado else 40))
                if modo_pistola: pygame.draw.rect(pantalla, NEGRO, (j1_x - 10, j1_y_dib + 10, 10, 20))
                if modo_escudo:
                    pygame.draw.circle(pantalla, VERDE, (j1_x+20, j1_y_dib+20), 45, 4)
                    pantalla.blit(fuente_chica.render(f"{int(escudo_timer - time.time())}s", True, VERDE), (j1_x+5, j1_y_dib-20))
                elif escudo_c_j1_activo: pygame.draw.circle(pantalla, CIAN, (j1_x+20, j1_y_dib+20), 48, 5)
                pygame.draw.rect(pantalla, color_p1, (dog1_x, dog1_y, 15, 15))
            if j2_vivo:
                pygame.draw.rect(pantalla, color_j2, (j2_x, j2_y_dib, 40, 20 if j2_agachado else 40))
                if j2_modo_pistola: pygame.draw.rect(pantalla, NEGRO, (j2_x - 10, j2_y_dib + 10, 10, 20))
                if j2_modo_escudo:
                    pygame.draw.circle(pantalla, VERDE, (j2_x+20, j2_y_dib+20), 45, 4)
                    pantalla.blit(fuente_chica.render(f"{int(j2_escudo_timer - time.time())}s", True, VERDE), (j2_x+5, j2_y_dib-20))
                elif escudo_e_j2_activo: pygame.draw.circle(pantalla, BLANCO, (j2_x+20, j2_y_dib+20), 48, 5)
                pygame.draw.rect(pantalla, color_p2, (dog2_x, dog2_y, 15, 15))

            if brillo > 0:
                overlay = pygame.Surface((ANCHO, ALTO)); overlay.set_alpha(brillo); overlay.fill(NEGRO)
                pantalla.blit(overlay, (0,0))

            txt_hud = f"Puntos: {puntaje} | Nivel: {nivel}/500 | Balas: {balas_restantes}"
            if modo_pistola: txt_hud += f" | Asalto J1: {balas_pistola}"
            if j2_modo_pistola: txt_hud += f" | Asalto J2: {j2_balas_pistola}"
            pantalla.blit(fuente.render(txt_hud, True, BLANCO), (20, 20))

            # Controles táctiles SIEMPRE visibles durante juego
            # dibujar_botones_tactil(pantalla, modo='juego')  # desactivado: jugar solo con teclado/táctil sin HUD

            if pausado:
                s_pausa = pygame.Surface((ANCHO, ALTO)); s_pausa.set_alpha(150); s_pausa.fill(NEGRO)
                pantalla.blit(s_pausa, (0,0))
                txt_pausa = fuente_gigante.render("PAUSA", True, BLANCO)
                pantalla.blit(txt_pausa, (ANCHO//2 - txt_pausa.get_width()//2, ALTO//2 - 50))
            elif tiempo_congelado:
                pantalla.blit(fuente_gigante.render("¡TIEMPO CONGELADO!", True, CIAN), (50, ALTO//2))

        if estado_juego == "PERDISTE" or estado_juego == "VICTORIA":
            s = pygame.Surface((ANCHO, ALTO)); s.set_alpha(150); s.fill(NEGRO)
            pantalla.blit(s, (0,0))
            if estado_juego == "PERDISTE":
                txt_final = fuente_gigante.render("GAME OVER", True, ROJO)
            else:
                txt_final = fuente_gigante.render("¡ERES UNA LEYENDA!", True, AMARILLO)
            pantalla.blit(txt_final, (ANCHO//2 - txt_final.get_width()//2, ALTO//2 - 150))
            txt_puntos = fuente_grande.render(f"Puntaje Final: {puntaje}", True, BLANCO)
            pantalla.blit(txt_puntos, (ANCHO//2 - txt_puntos.get_width()//2, ALTO//2 - 50))

            if t_actual - ultimo_click_menu > 0.5:
                if dibujar_boton("JUGAR DE NUEVO", ANCHO//2 - 200, ALTO//2 + 40, 400, 60, VERDE, (100, 255, 100)):
                    iniciar_juego(modo_dos_jugadores); ultimo_click_menu = t_actual
                if dibujar_boton("VOLVER AL MENÚ", ANCHO//2 - 150, ALTO//2 + 120, 300, 50, BLANCO, GRIS, "chica"):
                    estado_juego = "MENU"; ultimo_click_menu = t_actual
            else:
                dibujar_boton("JUGAR DE NUEVO", ANCHO//2 - 200, ALTO//2 + 40, 400, 60, VERDE, (100, 255, 100))
                dibujar_boton("VOLVER AL MENÚ", ANCHO//2 - 150, ALTO//2 + 120, 300, 50, BLANCO, GRIS, "chica")

        # --- BLIT FINAL ---
        if estado_juego not in ["MENU", "SELECCION_JUGADORES", "AJUSTES", "CONTROLES", "COLOR_PICKER"]:
            ox, oy = (random.randint(-temblor, temblor), random.randint(-temblor, temblor)) if temblor > 0 and not pausado else (0,0)
            if temblor > 0 and not pausado: temblor -= 1
            pantalla_real.fill(NEGRO)
            pantalla_real.blit(pantalla, (ox, oy))
        else:
            pantalla_real.fill(NEGRO)
            pantalla_real.blit(pantalla, (0, 0))

        pygame.display.flip()
        reloj.tick(60)
        await asyncio.sleep(0)  # ← ESENCIAL para Pygbag

    pygame.quit()


asyncio.run(main())
