def get_descendant_category_ids(category) -> list[int]:
    """
    Returns the ids of all descendant categories of the given category
    """
    category_ids = []
    categories = [category]
    while categories:
        child_categories = []
        for category in categories:
            category_ids.append(category.id)
            child_categories.extend(list(category.child_id))
        categories = child_categories
    return category_ids