from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verification.status_calculator import (
    ClaimStatus,
    ClaimVerdict,
    EventStatus,
    calculate_status,
)


def claim(status, is_key=True, support=0, refuted=False):
    return ClaimVerdict(status=status, is_key=is_key, independent_support=support, direct_refutation=refuted)


def test_all_confirmed():
    result = calculate_status([claim(ClaimStatus.CONFIRMED), claim(ClaimStatus.CONFIRMED)])
    assert result.status == EventStatus.CONFIRMED


def test_partial_confirmed():
    result = calculate_status([claim(ClaimStatus.CONFIRMED), claim(ClaimStatus.UNCONFIRMED)])
    assert result.status == EventStatus.PARTIAL


def test_refuted_with_direct_quote():
    result = calculate_status([claim(ClaimStatus.REFUTED, refuted=True)])
    assert result.status == EventStatus.REFUTED


def test_conflicting_wins_over_confirmed():
    result = calculate_status([claim(ClaimStatus.CONFIRMED), claim(ClaimStatus.CONFLICTING)])
    assert result.status == EventStatus.CONFLICTING


def test_unconfirmed_is_not_refuted():
    result = calculate_status([claim(ClaimStatus.UNCONFIRMED)])
    assert result.status == EventStatus.UNCONFIRMED


def test_needs_check_when_not_checked():
    result = calculate_status([claim(ClaimStatus.CONFIRMED), claim(ClaimStatus.NOT_CHECKED)])
    assert result.status == EventStatus.NEEDS_CHECK


def test_non_key_claims_do_not_block_publication():
    result = calculate_status(
        [claim(ClaimStatus.CONFIRMED), claim(ClaimStatus.UNCONFIRMED, is_key=False)]
    )
    assert result.status == EventStatus.CONFIRMED
