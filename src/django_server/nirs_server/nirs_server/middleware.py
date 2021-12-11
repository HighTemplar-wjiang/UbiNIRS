# UbiNIRS middleware.


class UbiNIRSMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if "NIRS-Can-Scan" not in response:
            response["NIRS-Can-Scan"] = "false"

        if "New-Transaction" not in response:
            response["New-Transaction"] = "false"

        return response
