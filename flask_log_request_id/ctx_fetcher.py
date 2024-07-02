class ExecutedOutsideContext(Exception):
    """
    Exception to be raised if a fetcher was called outside its context
    """
    pass


class MultiContextRequestIdFetcher:
    def __init__(self):
        self.fetchers = []

    def register_fetcher(self, fetcher):
        self.fetchers.append(fetcher)

    def get_request_id(self):
        for fetcher in self.fetchers:
            try:
                request_id = fetcher()
                if request_id:
                    return request_id
            except Exception as e:
                print(f"Error fetching request ID: {e}")
        return None