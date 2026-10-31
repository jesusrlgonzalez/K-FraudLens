# FraudLens · Inteligencia de riesgo transaccional

**Transformar datos transaccionales en información confiable para identificar operaciones que requieren investigación, reduciendo la incertidumbre de los equipos de análisis de riesgo.**

## Qué resuelve
Procesar datos transaccionales, identificar inconsistencias, evaluar patrones sospechosos y generar recomendaciones documentadas para revisión humana, sin bloquear operaciones automáticamente.

Auditoría de calidad de eventos transaccionales (12 reglas: duplicados, relojes, importes, monedas, identificadores inseguros…) y experimento de priorización para revisión de riesgo, con etiquetas aisladas para evitar fuga.

## Hacia dónde va
Convertirse en una solución de referencia para análisis de riesgo transaccional basado en modelos explicables, trazabilidad y evaluación económica de las decisiones.

**Objetivo:** Desarrollar y validar modelos de clasificación desbalanceada que permitan comparar la priorización de alertas frente a reglas tradicionales, considerando precisión, recuperación y costos de revisión.

**Valor que persigue:** Disminuir investigaciones improductivas y mejorar la asignación de recursos de análisis de riesgo.

## Resultados de la demo
Sobre un conjunto de datos sintéticos diseñado con errores y casos difíciles: **3 200 eventos: 3 055 candidatos, 36 a revisión, 109 en cuarentena; conservación verificada y sin acceso a etiquetas en la auditoría**.

## Pruébalo en 2 minutos
```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py test     # 71 tests automatizados
python run.py demo     # demo de punta a punta → demo_output/
python run.py api      # API REST → http://127.0.0.1:8000/docs
```

## Diseñado para decisiones responsables
- **Siempre con una persona al mando:** no bloquea pagos ni acusa a personas; una decisión de calidad no es un veredicto de fraude.
- **Trazable:** cada registro conserva su motivo de aceptación, revisión o cuarentena.
- **Probado:** 71 tests automatizados en Linux y Windows en cada cambio.
- **Contenedor:** la imagen Docker se construye en cada cambio.

## Estado
Prototipo funcional demostrado con datos sintéticos. El siguiente paso es un **piloto con datos reales** de su organización, bajo acuerdo de uso y confidencialidad.

**¿Le interesa un piloto?** Contacte a **Kriter Systems**.

---
I29 · Kriter Systems · Los datos incluidos son sintéticos y no representan a personas ni empresas reales.
