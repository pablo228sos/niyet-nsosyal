from niyet.allocator import allocate
from niyet.types import CandidateMatch, IntentType, Responder


responders = [
    Responder("r1", ("robotics", "control"), (IntentType.ASK,), 1),
    Responder("r2", ("python", "ml"), (IntentType.ASK, IntentType.FEEDBACK), 2),
    Responder("r3", ("design",), (IntentType.FEEDBACK,), 1),
]

matches = [
    CandidateMatch("pid-help", "r1", 0.98, 0.95, 0.90),
    CandidateMatch("pid-help", "r2", 0.35, 0.80, 0.70),
    CandidateMatch("python-help", "r2", 0.96, 0.95, 0.88),
    CandidateMatch("ui-feedback", "r3", 0.97, 0.90, 0.85),
    CandidateMatch("ui-feedback", "r2", 0.45, 0.75, 0.65),
]

for assignment in allocate(matches, responders):
    print(
        f"{assignment.intent_id:15} -> {assignment.responder_id} "
        f"score={assignment.score:.3f}"
    )
