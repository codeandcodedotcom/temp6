@pytest.fixture(autouse=True)
def patch_async_session(monkeypatch):
    async def dummy_session():
        class DummySession:
            async def __aenter__(self): return self
            async def __aexit__(self, exc_type, exc, tb): pass
        yield DummySession()

    app.dependency_overrides[
        "app.db.session_new.get_db_session"
    ] = dummy_session

    yield

    app.dependency_overrides = {}
