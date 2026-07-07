from src.auth.pkce import generate_code_challenge, generate_code_verifier


def test_pkce_verifier_and_challenge_generation():
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)

    assert 43 <= len(verifier) <= 128
    assert len(challenge) == 43
    assert "=" not in challenge
    assert generate_code_challenge(verifier) == challenge
