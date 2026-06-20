import discord
from discord.ext import tasks
from datetime import datetime, timedelta
import pytz
import os

TOKEN = os.getenv("DISCORD_TOKEN")

CANAL_ID = 1517908909484933140
CARGO_ID = 1517910050889400340

fuso = pytz.timezone("America/Sao_Paulo")

agenda = {
    "monday": ["12:15", "17:30"],
    "tuesday": ["13:00", "19:00"],
    "wednesday": ["10:00", "16:00"],
    "thursday": ["14:00", "20:15"],
    "friday": ["15:00", "21:00"],
    "saturday": ["10:30", "16:30"],
    "sunday": ["16:45", "23:30"],
}

dias_pt = {
    "monday": "segunda-feira",
    "tuesday": "terça-feira",
    "wednesday": "quarta-feira",
    "thursday": "quinta-feira",
    "friday": "sexta-feira",
    "saturday": "sábado",
    "sunday": "domingo",
}

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

avisos_enviados = set()
bot_ativo = True


def get_eventos_de_hoje():
    agora = datetime.now(fuso)
    dia_en = agora.strftime("%A").lower()
    return dia_en, agenda.get(dia_en, [])


def proxima_invasao():
    agora = datetime.now(fuso)
    proximos = []

    for i in range(8):
        dia_data = agora + timedelta(days=i)
        dia_en = dia_data.strftime("%A").lower()

        for horario in agenda.get(dia_en, []):
            hora_evento = datetime.strptime(horario, "%H:%M")
            evento = dia_data.replace(
                hour=hora_evento.hour,
                minute=hora_evento.minute,
                second=0,
                microsecond=0
            )

            if evento > agora:
                proximos.append((evento, dia_en, horario))

    proximos.sort(key=lambda x: x[0])
    return proximos[0] if proximos else None


@client.event
async def on_ready():
    print(f"Bot online como {client.user}")

    if not verificar_eventos.is_running():
        verificar_eventos.start()


@client.event
async def on_message(message):
    global bot_ativo

    if message.author.bot:
        return

    comando = message.content.lower().strip()

    if comando == "!proximainvasao":
        prox = proxima_invasao()

        if not prox:
            await message.channel.send("❌ Não encontrei nenhuma próxima invasão.")
            return

        evento, dia_en, horario = prox

        await message.channel.send(
            "📌 **Próxima invasão:**\n"
            f"📅 Dia: {dias_pt[dia_en]}\n"
            f"🕒 Horário: {horario}\n"
            f"⏳ Data: {evento.strftime('%d/%m/%Y %H:%M')}"
        )

    elif comando == "!agenda":
        texto = "📅 **Agenda semanal de invasões:**\n\n"

        for dia_en, horarios in agenda.items():
            texto += f"**{dias_pt[dia_en].capitalize()}**: {', '.join(horarios)}\n"

        await message.channel.send(texto)

    elif comando == "!pararbot":
        bot_ativo = False
        await message.channel.send("⛔ Avisos de invasão pausados.")

    elif comando == "!iniciarbot":
        bot_ativo = True
        await message.channel.send("✅ Avisos de invasão ativados novamente.")


@tasks.loop(seconds=30)
async def verificar_eventos():
    if not bot_ativo:
        return

    agora = datetime.now(fuso)
    dia_en, horarios = get_eventos_de_hoje()

    canal = client.get_channel(CANAL_ID)

    if canal is None:
        print("Canal não encontrado. Verifique o CANAL_ID.")
        return

    for horario in horarios:
        hora_evento = datetime.strptime(horario, "%H:%M")
        evento_hoje = agora.replace(
            hour=hora_evento.hour,
            minute=hora_evento.minute,
            second=0,
            microsecond=0
        )

        avisos = [
            (evento_hoje - timedelta(minutes=5), "⏰ A invasão começa em 5 minutos!"),
            (evento_hoje, "🚨 A invasão começou agora!")
        ]

        for horario_aviso, mensagem in avisos:
            chave = f"{agora.strftime('%Y-%m-%d')}-{horario}-{mensagem}"

            if chave in avisos_enviados:
                continue

            if agora.strftime("%H:%M") == horario_aviso.strftime("%H:%M"):
                mencao = f"<@&{CARGO_ID}> " if CARGO_ID else ""

                await canal.send(
                    f"{mencao}{mensagem}\n"
                    f"📅 Dia: {dias_pt[dia_en]}\n"
                    f"🕒 Horário: {horario}"
                )

                avisos_enviados.add(chave)


if not TOKEN:
    print("ERRO: DISCORD_TOKEN não encontrado nas variáveis do Railway.")
else:
    client.run(TOKEN)
