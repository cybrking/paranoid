from app.members import Store


def team():
    store = Store()
    store.set("w1", "olive", "owner")
    store.set("w1", "ada", "admin")
    store.set("w1", "bob", "member")
    store.set("w1", "cy", "member")
    store.set("w2", "mallory", "owner")
    store.set("w2", "max", "admin")
    return store
