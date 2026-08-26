from app.domain.schema import PredictionResult
from app.evaluation.evaluator import ModelEvaluator
def p(noise): return PredictionResult.model_validate({"emotional_tone":"neutral","emotional_intensity":"low","background_noise_present":bool(noise),"background_noise_type":noise,"background_noise_severity":"low" if noise else "none","audio_quality":"clear","speaker_overlap_present":False,"long_silence_present":False,"confidence":0.5})
def test_noise_type_accuracy_is_measured(): assert ModelEvaluator.evaluate({"a":p("TV")},{"a":p("road noise")})["background_noise_type_accuracy"] == 0.0
