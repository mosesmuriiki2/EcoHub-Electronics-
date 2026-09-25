from .models import Product


def generate_sku(category=None):
    """
    Generate a unique SKU in the form PREFIX-0001, where PREFIX is the
    first 3 alphanumeric characters of the category name (uppercased),
    or 'GEN' if there's no category.
    """
    if category and category.name:
        letters = ''.join(ch for ch in category.name if ch.isalnum())
        prefix = (letters[:3] or 'GEN').upper()
    else:
        prefix = 'GEN'

    # Find the highest existing numeric suffix for this prefix
    existing_skus = Product.objects.filter(
        sku__startswith=f'{prefix}-'
    ).values_list('sku', flat=True)

    max_num = 0
    for sku in existing_skus:
        suffix = sku[len(prefix) + 1:]
        if suffix.isdigit():
            max_num = max(max_num, int(suffix))

    candidate = f'{prefix}-{max_num + 1:04d}'

    # Safety net in case of any gap/race - keep incrementing until free
    next_num = max_num + 1
    while Product.objects.filter(sku=candidate).exists():
        next_num += 1
        candidate = f'{prefix}-{next_num:04d}'

    return candidate