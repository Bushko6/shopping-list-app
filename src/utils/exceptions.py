class ShoppingListNotFoundError(KeyError):
    pass


class ShoppingItemNotFoundError(KeyError):
    pass


class ListArchivedError(ValueError):
    pass


class ItemAlreadyPurchasedError(ValueError):
    pass


class ItemNotPurchasedError(ValueError):
    pass
