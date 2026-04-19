"""Herramientas de datos de mercado y trading."""
from __future__ import annotations
import json
import os
from datetime import datetime, timedelta
import httpx

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_PAPER = os.getenv("ALPACA_PAPER", "true").lower() == "true"
ALPACA_BASE = "https://paper-api.alpaca.markets" if ALPACA_PAPER else "https://api.alpaca.markets"

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET = os.getenv("BINANCE_SECRET_KEY", "")


TOOLS_MARKET: list[dict] = [
    {
        "name": "mercado_cotizacion",
        "description": (
            "Obtiene precio actual, volumen y cambio diario de un activo. "
            "Funciona para acciones (AAPL, TSLA, AMZN), ETFs (SPY, QQQ) y crypto (BTC-USD, ETH-USD)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Símbolo del activo, ej: AAPL, BTC-USD, SPY, AMZN",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "mercado_historico",
        "description": (
            "Descarga precios históricos de un activo para analizar tendencias. "
            "Devuelve OHLCV (apertura, máximo, mínimo, cierre, volumen) y calcula "
            "indicadores técnicos: SMA20, SMA50, RSI, MACD."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "periodo": {
                    "type": "string",
                    "description": "Período de tiempo",
                    "enum": ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                    "default": "3mo",
                },
                "intervalo": {
                    "type": "string",
                    "description": "Intervalo entre velas",
                    "enum": ["1d", "1wk", "1mo"],
                    "default": "1d",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "mercado_analisis_tecnico",
        "description": (
            "Realiza un análisis técnico completo de un activo: tendencia, soporte/resistencia, "
            "señales de compra/venta basadas en indicadores (RSI, MACD, Medias Móviles, Bollinger). "
            "Devuelve una señal clara: COMPRAR, VENDER o MANTENER con explicación."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "periodo": {
                    "type": "string",
                    "enum": ["1mo", "3mo", "6mo", "1y"],
                    "default": "3mo",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "mercado_screener",
        "description": (
            "Busca activos que cumplan ciertos criterios: acciones con RSI sobrevendido, "
            "crypto con momentum positivo, ETFs de un sector específico, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "description": "Tipo de activo a buscar",
                    "enum": ["acciones_usa", "crypto", "etf", "mexico"],
                },
                "criterio": {
                    "type": "string",
                    "description": "Criterio de filtro, ej: 'RSI bajo 30', 'tendencia alcista', 'dividendos altos'",
                },
            },
            "required": ["tipo", "criterio"],
        },
    },
    {
        "name": "trading_paper_trade",
        "description": (
            "Registra una operación de paper trading (simulada, sin dinero real) para practicar y validar estrategias. "
            "Guarda la operación con precio de entrada, stop loss y take profit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "accion": {"type": "string", "enum": ["COMPRAR", "VENDER"]},
                "cantidad": {"type": "number", "description": "Número de acciones o unidades"},
                "precio_entrada": {"type": "number", "description": "Precio actual de entrada"},
                "stop_loss": {"type": "number", "description": "Precio de stop loss (para limitar pérdidas)"},
                "take_profit": {"type": "number", "description": "Precio objetivo de ganancia"},
                "razon": {"type": "string", "description": "Por qué se hace esta operación"},
            },
            "required": ["ticker", "accion", "cantidad", "precio_entrada", "razon"],
        },
    },
    {
        "name": "trading_orden_real",
        "description": (
            "⚠️ EJECUTA UNA ORDEN REAL via Alpaca. "
            "Solo usar cuando el usuario lo confirme explícitamente. "
            "Requiere ALPACA_API_KEY y ALPACA_SECRET_KEY configurados. "
            "Por defecto opera en paper trading (simulado). "
            "Para activar dinero real: ALPACA_PAPER=false en .env."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "lado": {"type": "string", "enum": ["buy", "sell"]},
                "cantidad": {"type": "number"},
                "tipo_orden": {
                    "type": "string",
                    "enum": ["market", "limit"],
                    "default": "market",
                },
                "precio_limite": {
                    "type": "number",
                    "description": "Precio límite (solo para tipo_orden=limit)",
                },
            },
            "required": ["ticker", "lado", "cantidad"],
        },
    },
    {
        "name": "trading_portfolio",
        "description": "Muestra el portafolio actual y posiciones abiertas en Alpaca (paper o real).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    handlers = {
        "mercado_cotizacion": _cotizacion,
        "mercado_historico": _historico,
        "mercado_analisis_tecnico": _analisis_tecnico,
        "mercado_screener": _screener,
        "trading_paper_trade": _paper_trade,
        "trading_orden_real": _orden_real,
        "trading_portfolio": _portfolio,
    }
    if nombre not in handlers:
        return f"Herramienta desconocida: {nombre}"
    try:
        return handlers[nombre](**parametros)
    except Exception as exc:
        return f"Error en {nombre}: {exc}"


def _cotizacion(ticker: str) -> str:
    try:
        import yfinance as yf
        t = yf.Ticker(ticker.upper())
        info = t.fast_info
        hist = t.history(period="2d")
        if hist.empty:
            return f"No se encontraron datos para {ticker}."
        precio_actual = hist["Close"].iloc[-1]
        precio_anterior = hist["Close"].iloc[-2] if len(hist) > 1 else precio_actual
        cambio = precio_actual - precio_anterior
        cambio_pct = (cambio / precio_anterior) * 100
        volumen = hist["Volume"].iloc[-1]
        return (
            f"{'📈' if cambio >= 0 else '📉'} {ticker.upper()}\n"
            f"Precio: ${precio_actual:,.2f}\n"
            f"Cambio: {cambio:+.2f} ({cambio_pct:+.2f}%)\n"
            f"Volumen: {int(volumen):,}\n"
            f"Max 52s: ${getattr(info, 'year_high', '—')}\n"
            f"Min 52s: ${getattr(info, 'year_low', '—')}"
        )
    except ImportError:
        return "Instala yfinance: pip install yfinance"


def _historico(ticker: str, periodo: str = "3mo", intervalo: str = "1d") -> str:
    try:
        import yfinance as yf
        import pandas as pd
        df = yf.download(ticker.upper(), period=periodo, interval=intervalo, progress=False)
        if df.empty:
            return f"No hay datos históricos para {ticker}."
        # Indicadores básicos
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()
        # RSI
        delta = df["Close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
        ultimo = df.iloc[-1]
        precio_inicio = df["Close"].iloc[0]
        precio_fin = df["Close"].iloc[-1]
        rendimiento = ((precio_fin - precio_inicio) / precio_inicio) * 100
        return (
            f"{ticker.upper()} — {periodo} ({intervalo})\n"
            f"Precio actual: ${float(precio_fin):,.2f}\n"
            f"Rendimiento período: {rendimiento:+.2f}%\n"
            f"SMA20: ${float(ultimo['SMA20']):,.2f}\n"
            f"SMA50: ${float(ultimo['SMA50']):,.2f}\n"
            f"RSI(14): {float(ultimo['RSI']):.1f}\n"
            f"Tendencia: {'↑ ALCISTA' if float(ultimo['SMA20']) > float(ultimo['SMA50']) else '↓ BAJISTA'}"
        )
    except ImportError:
        return "Instala yfinance: pip install yfinance"


def _analisis_tecnico(ticker: str, periodo: str = "3mo") -> str:
    try:
        import yfinance as yf
        df = yf.download(ticker.upper(), period=periodo, interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return f"Datos insuficientes para analizar {ticker}."
        close = df["Close"].squeeze()
        # Medias móviles
        sma20 = float(close.rolling(20).mean().iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1]) if len(df) >= 50 else None
        precio = float(close.iloc[-1])
        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = float((100 - (100 / (1 + gain / loss))).iloc[-1])
        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = float((ema12 - ema26).iloc[-1])
        signal_line = float((ema12 - ema26).ewm(span=9).mean().iloc[-1])
        # Bollinger
        sma20_ser = close.rolling(20).mean()
        std20 = float(close.rolling(20).std().iloc[-1])
        bb_upper = float(sma20_ser.iloc[-1]) + 2 * std20
        bb_lower = float(sma20_ser.iloc[-1]) - 2 * std20
        # Señal
        puntos = 0
        razones = []
        if rsi < 30:
            puntos += 2
            razones.append(f"RSI={rsi:.0f} → sobreventa (señal alcista)")
        elif rsi > 70:
            puntos -= 2
            razones.append(f"RSI={rsi:.0f} → sobrecompra (señal bajista)")
        if precio > sma20:
            puntos += 1
            razones.append(f"Precio sobre SMA20 (tendencia corto plazo alcista)")
        else:
            puntos -= 1
            razones.append(f"Precio bajo SMA20 (tendencia corto plazo bajista)")
        if sma50 and sma20 > sma50:
            puntos += 1
            razones.append("SMA20 > SMA50 (golden cross — alcista)")
        elif sma50 and sma20 < sma50:
            puntos -= 1
            razones.append("SMA20 < SMA50 (death cross — bajista)")
        if macd > signal_line:
            puntos += 1
            razones.append("MACD sobre señal (momentum alcista)")
        else:
            puntos -= 1
            razones.append("MACD bajo señal (momentum bajista)")
        if precio < bb_lower:
            puntos += 1
            razones.append("Precio bajo Bollinger inferior (posible rebote)")
        elif precio > bb_upper:
            puntos -= 1
            razones.append("Precio sobre Bollinger superior (posible corrección)")
        if puntos >= 2:
            señal = "🟢 COMPRAR"
        elif puntos <= -2:
            señal = "🔴 VENDER / SHORT"
        else:
            señal = "🟡 MANTENER / ESPERAR"
        return (
            f"ANÁLISIS TÉCNICO — {ticker.upper()}\n"
            f"Precio: ${precio:,.2f}\n"
            f"RSI(14): {rsi:.1f} | MACD: {macd:+.3f}\n"
            f"SMA20: ${sma20:,.2f}" +
            (f" | SMA50: ${sma50:,.2f}" if sma50 else "") +
            f"\nBollinger: ${bb_lower:,.2f} – ${bb_upper:,.2f}\n"
            f"\nSEÑAL: {señal} (score: {puntos:+d})\n"
            f"\nRazones:\n" + "\n".join(f"  • {r}" for r in razones)
        )
    except ImportError:
        return "Instala yfinance: pip install yfinance"


def _screener(tipo: str, criterio: str) -> str:
    listas = {
        "acciones_usa": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "BAC", "XOM"],
        "crypto": ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "ADA-USD", "XRP-USD"],
        "etf": ["SPY", "QQQ", "IWM", "GLD", "TLT", "VTI", "ARKK", "XLE", "XLF"],
        "mexico": ["AMXL.MX", "WALMEX.MX", "FEMSAUBD.MX", "GFINBURO.MX", "BIMBOA.MX"],
    }
    tickers = listas.get(tipo, listas["acciones_usa"])
    return (
        f"Screener: {tipo} | Criterio: {criterio}\n"
        f"Tickers a analizar: {', '.join(tickers)}\n\n"
        f"Ejecuta mercado_analisis_tecnico para cada uno y filtra según el criterio indicado."
    )


_paper_trades: list[dict] = []


def _paper_trade(
    ticker: str,
    accion: str,
    cantidad: float,
    precio_entrada: float,
    razon: str,
    stop_loss: float | None = None,
    take_profit: float | None = None,
) -> str:
    operacion = {
        "id": len(_paper_trades) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ticker": ticker.upper(),
        "accion": accion,
        "cantidad": cantidad,
        "precio_entrada": precio_entrada,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "valor_total": cantidad * precio_entrada,
        "razon": razon,
        "estado": "ABIERTA",
    }
    _paper_trades.append(operacion)
    riesgo = f"${abs(precio_entrada - stop_loss) * cantidad:,.2f}" if stop_loss else "No definido"
    potencial = f"${abs(take_profit - precio_entrada) * cantidad:,.2f}" if take_profit else "No definido"
    return (
        f"📝 Paper Trade registrado #{operacion['id']}\n"
        f"{accion} {cantidad} {ticker.upper()} @ ${precio_entrada:,.2f}\n"
        f"Valor total: ${operacion['valor_total']:,.2f}\n"
        f"Stop Loss: ${stop_loss:,.2f} | Riesgo: {riesgo}\n"
        f"Take Profit: ${take_profit:,.2f} | Potencial: {potencial}\n"
        f"Razón: {razon}"
    )


def _orden_real(
    ticker: str,
    lado: str,
    cantidad: float,
    tipo_orden: str = "market",
    precio_limite: float | None = None,
) -> str:
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        return (
            "⚠️ ALPACA no configurado. Agrega ALPACA_API_KEY y ALPACA_SECRET_KEY en tu .env.\n"
            "Regístrate en alpaca.markets (gratis para paper trading)."
        )
    modo = "PAPER TRADING (simulado)" if ALPACA_PAPER else "⚠️ DINERO REAL"
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
    }
    body: dict = {
        "symbol": ticker.upper(),
        "qty": str(cantidad),
        "side": lado,
        "type": tipo_orden,
        "time_in_force": "gtc",
    }
    if tipo_orden == "limit" and precio_limite:
        body["limit_price"] = str(precio_limite)
    resp = httpx.post(f"{ALPACA_BASE}/v2/orders", json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    orden = resp.json()
    return (
        f"✅ Orden enviada [{modo}]\n"
        f"ID: {orden.get('id', '—')}\n"
        f"{lado.upper()} {cantidad} {ticker.upper()} — {tipo_orden}\n"
        f"Estado: {orden.get('status', '—')}"
    )


def _portfolio() -> str:
    if not ALPACA_API_KEY:
        return "⚠️ ALPACA no configurado. Agrega ALPACA_API_KEY en tu .env."
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
    }
    modo = "PAPER" if ALPACA_PAPER else "REAL"
    cuenta = httpx.get(f"{ALPACA_BASE}/v2/account", headers=headers, timeout=20).json()
    posiciones = httpx.get(f"{ALPACA_BASE}/v2/positions", headers=headers, timeout=20).json()
    lineas = [
        f"Portfolio Alpaca [{modo}]",
        f"Valor total: ${float(cuenta.get('portfolio_value', 0)):,.2f}",
        f"Cash: ${float(cuenta.get('cash', 0)):,.2f}",
        f"P&L día: ${float(cuenta.get('equity', 0)) - float(cuenta.get('last_equity', 0)):+,.2f}",
        "",
        f"Posiciones abiertas ({len(posiciones)}):",
    ]
    for p in posiciones:
        pl = float(p.get("unrealized_pl", 0))
        lineas.append(
            f"  {p['symbol']}: {p['qty']} uds @ ${float(p['avg_entry_price']):,.2f} "
            f"| P&L: ${pl:+,.2f}"
        )
    return "\n".join(lineas)
