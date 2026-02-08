"""
Wrapper para proveedores de IA.
Actualmente soporta Gemini Flash. Preparado para conectar con otros proveedores.
"""
import time
import logging

logger = logging.getLogger(__name__)


def get_ai_client(config):
    """Obtiene el cliente de IA según la configuración"""
    if config.ai_provider == 'gemini_flash':
        return GeminiProvider(config)
    raise ValueError(f"Proveedor de IA no soportado: {config.ai_provider}")


class GeminiProvider:
    """Wrapper para Google Gemini Flash"""

    def __init__(self, config):
        self.config = config
        self.model_name = config.ai_model or 'gemini-2.0-flash'
        self._client = None

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self.config.ai_api_key)
            self._client = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    'max_output_tokens': self.config.max_tokens_per_request,
                    'temperature': 0.7,
                }
            )
        return self._client

    def generate_response(self, prompt, context=None):
        """
        Genera una respuesta usando Gemini Flash.
        Retorna dict con: respuesta, tokens_input, tokens_output, latencia_ms, exitoso, error
        """
        from asistente.models import AIUsageLog, ChatSession

        start_time = time.time()
        result = {
            'respuesta': '',
            'tokens_input': 0,
            'tokens_output': 0,
            'latencia_ms': 0,
            'exitoso': False,
            'error': '',
        }

        try:
            client = self._get_client()

            # Construir el prompt completo
            full_prompt = prompt
            if context and context.get('system_prompt'):
                full_prompt = f"{context['system_prompt']}\n\n{prompt}"

            response = client.generate_content(full_prompt)

            elapsed_ms = int((time.time() - start_time) * 1000)

            result['respuesta'] = response.text
            result['latencia_ms'] = elapsed_ms
            result['exitoso'] = True

            # Obtener tokens si están disponibles
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                result['tokens_input'] = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
                result['tokens_output'] = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0

            # Log de uso
            session = context.get('session') if context else None
            AIUsageLog.objects.create(
                session=session,
                provider='gemini_flash',
                model=self.model_name,
                tokens_input=result['tokens_input'],
                tokens_output=result['tokens_output'],
                costo_estimado=self._calcular_costo(result['tokens_input'], result['tokens_output']),
                latencia_ms=elapsed_ms,
                exitoso=True,
            )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            result['latencia_ms'] = elapsed_ms
            result['error'] = str(e)
            logger.error(f"Error Gemini: {e}")

            # Log de error
            session = context.get('session') if context else None
            AIUsageLog.objects.create(
                session=session,
                provider='gemini_flash',
                model=self.model_name,
                tokens_input=0,
                tokens_output=0,
                costo_estimado=0,
                latencia_ms=elapsed_ms,
                exitoso=False,
                error_mensaje=str(e),
            )

        return result

    def classify_intent(self, texto, intents_disponibles):
        """
        Usa IA para clasificar el intent cuando los keywords no son suficientes.
        Retorna dict con: intent, confidence
        """
        intents_list = ', '.join(intents_disponibles)
        prompt = (
            f"Clasificá la siguiente consulta de un usuario en UNA de estas categorías: {intents_list}, fuera_dominio.\n"
            f"El contexto es una empresa de Revisión Técnica Vehicular (RTV/RTO/VTV).\n"
            f"Respondé SOLO con el nombre de la categoría, nada más.\n\n"
            f"Consulta: \"{texto}\""
        )

        result = self.generate_response(prompt)
        if result['exitoso']:
            intent = result['respuesta'].strip().lower().replace(' ', '_')
            # Validar que sea un intent conocido
            if intent in intents_disponibles or intent == 'fuera_dominio':
                return {'intent': intent, 'confidence': 0.8}
        return {'intent': 'fuera_dominio', 'confidence': 0.5}

    def is_in_domain(self, texto):
        """Verifica si la consulta está dentro del dominio de RTV"""
        prompt = (
            "¿La siguiente consulta está relacionada con revisión técnica vehicular, "
            "turnos, tarifas, ubicación de talleres o servicios de RTV/RTO/VTV? "
            "Respondé SOLO 'SI' o 'NO'.\n\n"
            f"Consulta: \"{texto}\""
        )
        result = self.generate_response(prompt)
        if result['exitoso']:
            return result['respuesta'].strip().upper().startswith('SI')
        return False

    def _calcular_costo(self, tokens_input, tokens_output):
        """Calcula costo estimado para Gemini Flash (precios aproximados)"""
        # Gemini Flash: ~$0.075/1M input, ~$0.30/1M output
        costo_input = (tokens_input / 1_000_000) * 0.075
        costo_output = (tokens_output / 1_000_000) * 0.30
        return round(costo_input + costo_output, 6)


def test_connection(config):
    """Prueba la conexión con el proveedor de IA. Retorna (exitoso, mensaje)"""
    try:
        provider = get_ai_client(config)
        result = provider.generate_response("Respondé solo 'OK' para confirmar que funciona.")
        if result['exitoso']:
            return True, f"Conexión exitosa. Modelo: {config.ai_model}. Latencia: {result['latencia_ms']}ms"
        return False, f"Error: {result['error']}"
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"
