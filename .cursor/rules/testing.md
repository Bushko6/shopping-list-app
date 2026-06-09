# Testing Guide — Shopping List App

## Toolchain

| Tool | Purpose |
|---|---|
| `pytest >= 8` | Test runner |
| `pytest-cov >= 5` | Branch coverage via `--cov` |
| `pytest-mock >= 3.14` | `mocker` fixture / `MagicMock` helpers |

Install: `pip install -e ".[dev]"`

---

## TDD workflow (mandatory)

1. **Red** — write a test that describes the desired behaviour. Run it; confirm it fails.
2. **Green** — write the minimum implementation to make it pass.
3. **Refactor** — clean up without breaking tests.

Never commit production code that does not have a corresponding test written first.

---

## Test layout

```
tests/
  unit/
    models/      test_user.py, test_shopping_list.py, test_item.py,
                 test_category.py, test_purchase.py, test_budget_entry.py,
                 test_invite_request.py, test_enums.py
    storage/     test_user_repo.py, test_shopping_list_repo.py, test_item_repo.py,
                 test_category_repo.py, test_purchase_repo.py,
                 test_budget_entry_repo.py, test_invite_request_repo.py
    services/    test_sorting_strategies.py, test_events_observer.py,
                 test_notification.py, test_list_service.py,
                 test_item_service.py, test_share_service.py,
                 test_user_service.py
  integration/
    conftest.py                        (shared fixtures, Clock helper)
    test_list_item_workflow.py
    test_share_invite_workflow.py
    test_budget_blocking_workflow.py
```

Target: **200+ tests** total across both layers.

---

## Unit tests

Unit tests verify a single class in isolation. All collaborators are mocked.

```python
# tests/unit/services/test_item_service.py
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from services.item_service import ItemService
from services.sorting_strategies import AlphabeticSortStrategy

def test_purchase_item_creates_budget_entry_per_list_member():
    item_repo        = MagicMock()
    purchase_repo    = MagicMock()
    budget_entry_repo = MagicMock()
    list_repo        = MagicMock()
    category_repo    = MagicMock()
    user_repo        = MagicMock()
    bus              = MagicMock()

    added = datetime(2025, 10, 15)
    item_repo.get_by_id.return_value = Item(
        "i1", "l1", "Milk", 2, "L", "c1"
    )
    list_repo.get_by_id.return_value = ShoppingList(
        "l1", "Weekly Shop", owner_id="u1", created_at=added
    )

    svc = ItemService(
        item_repo, purchase_repo, budget_entry_repo,
        list_repo, category_repo, user_repo,
        AlphabeticSortStrategy(), bus,
        clock=lambda: added + timedelta(days=1),
    )
    purchase, entries = svc.purchase("i1", purchased_by="u1", actual_price=1.50)

    assert purchase is not None
    bus.notify_list_status.assert_called_once()
```

Rules:
- One `assert` per logical concept (multiple asserts for one scenario are fine).
- Never hit real storage — always inject mocks.
- Name tests `test_<method>_<scenario>_<expected_outcome>`.

---

## Integration tests

Integration tests wire real in-memory implementations together through the full stack
and verify end-to-end workflows.

```python
# tests/integration/test_list_item_workflow.py
from datetime import datetime, timedelta
from storage.memory.user_repo import InMemoryUserRepository
from storage.memory.shopping_list_repo import InMemoryShoppingListRepository
from storage.memory.item_repo import InMemoryItemRepository
from storage.memory.category_repo import InMemoryCategoryRepository
from storage.memory.purchase_repo import InMemoryPurchaseRepository
from storage.memory.budget_entry_repo import InMemoryBudgetEntryRepository
from services.sorting_strategies import AlphabeticSortStrategy
from services.events import EventBus
from services.item_service import ItemService

def test_purchase_item_stores_budget_entry():
    users         = InMemoryUserRepository()
    lists         = InMemoryShoppingListRepository()
    items         = InMemoryItemRepository()
    categories    = InMemoryCategoryRepository()
    purchases     = InMemoryPurchaseRepository()
    budget_entries = InMemoryBudgetEntryRepository()
    bus           = EventBus()
    added         = datetime(2025, 10, 15)

    users.add(User("u1", "Alice", "alice@example.com"))
    lists.add(ShoppingList("l1", "Weekly Shop", owner_id="u1", created_at=added))
    items.add(Item("i1", "l1", "Milk", 2, "L", "c1"))

    svc = ItemService(
        items, purchases, budget_entries, lists, categories, users,
        AlphabeticSortStrategy(), bus,
        clock=lambda: added + timedelta(days=1),
    )
    purchase, created = svc.purchase("i1", purchased_by="u1", actual_price=1.50)
    assert purchase is not None
    assert len(created) == 1
```

---

## Coverage

### Run locally

```bash
pytest --cov=src --cov-branch --cov-report=term-missing
```

### Generate all report formats (CI)

```bash
pytest \
  --cov=src \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov \
  --junitxml=junit.xml
```

### Artifacts

| File | Consumer |
|---|---|
| `coverage.xml` | SonarQube / SonarCloud |
| `junit.xml` | CI test-results panel |
| `htmlcov/` | Human review |

### Target

**Branch coverage >= 85%.** The assignment minimum is 70%; the extra margin accounts for
edge-case branches exposed during integration testing.

A branch is considered covered only when both the true and false paths are exercised.
Use `# pragma: no cover` sparingly and only for unreachable defensive guards.

---

## pytest-mock patterns

```python
# Spy on a method without replacing it
def test_event_fired_on_purchase(mocker):
    bus = EventBus()
    spy = mocker.spy(bus, "notify_list_status")
    ...
    spy.assert_called_once()

# Inject a controllable clock
def test_purchase_on_same_day_no_budget_warning():
    added = datetime(2025, 10, 15)
    svc = ItemService(..., clock=lambda: added)
    purchase, entries = svc.purchase("i1", purchased_by="u1", actual_price=1.00)
    assert entries == []
```

---

## What NOT to test

- `__init__.py` files (excluded from coverage via `pyproject.toml`).
- Third-party library internals.
- Pure data containers where the only logic is Python's own dataclass machinery.
