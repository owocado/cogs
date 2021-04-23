from redbot.core import commands


class HTTPCat(commands.Cog):
    """Fetch you an image card for a given standard HTTP status code, but as funnily expressed by cats, dogs and ducks."""

    __author__ = "<@306810730055729152>"
    __version__ = "0.0.4"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.standard_http_codes = [
            100, 101, 102, 103,
            200, 201, 202, 203, 204, 205, 206, 207, 208, 226,
            300, 301, 302, 303, 304, 305, 306, 307, 308,
            400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414,
            415, 416, 417, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 451,
            500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511,
        ]
        self.not_found_message = (
            "That doesn't look like a standard HTTP status code. You "
            "can find the list of all standard HTTP status codes over at:\n"
            "‣ <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status>\n"
            "‣ <https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml>\n"
            "‣ <https://tools.ietf.org/html/rfc7231#section-6>\n\n"
            "If you're trying to lookup for a HTTP status code which you received "
            "in a response that is not in this list, it is probably a non-standard "
            "HTTP response code, possibly custom to the server's software. "
            "You can also find a list of few non-standard HTTP status codes over at:\n"
            "<https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes>"
        )

    @commands.command(aliases=["hcat"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def httpcat(self, ctx: commands.Context, code: int):
        """Responds with HTTP cat image for a standard HTTP status code.

        HTTP response status codes indicate whether a specific HTTP request has been successfully completed.
        Responses are grouped in five classes:

        1xx (Informational): The request was received, continuing process.
        2xx (Successful): The request was successfully received, understood, and accepted.
        3xx (Redirects): Further action needs to be taken in order to complete the request.
        4xx (Client errors)The request contains bad syntax or cannot be fulfilled.
        5xx (Server errors): The server failed to fulfill an apparently valid request.
        """
        if code not in self.standard_http_codes:
            return await ctx.send(self.not_found_message)
        await ctx.send(f"https://http.cat/{code}")

    @commands.command(aliases=["hdog"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def httpdog(self, ctx: commands.Context, code: int):
        """Responds with HTTP dog image for a standard HTTP status code.

        HTTP response status codes indicate whether a specific HTTP request has been successfully completed.
        Responses are grouped in five classes:

        1xx (Informational): The request was received, continuing process.
        2xx (Successful): The request was successfully received, understood, and accepted.
        3xx (Redirects): Further action needs to be taken in order to complete the request.
        4xx (Client errors)The request contains bad syntax or cannot be fulfilled.
        5xx (Server errors): The server failed to fulfill an apparently valid request.
        """
        if code not in (self.standard_http_codes and [420, 444, 450, 451, 494, 509]):
            return await ctx.send(self.not_found_message)
        await ctx.send(f"https://httpstatusdogs.com/img/{code}.jpg")

    @commands.command(aliases=["hduck"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def httpduck(self, ctx: commands.Context, code: int):
        """Responds with HTTP duck image for a standard HTTP status code.

        HTTP response status codes indicate whether a specific HTTP request has been successfully completed.
        Responses are grouped in five classes:

        1xx (Informational): The request was received, continuing process.
        2xx (Successful): The request was successfully received, understood, and accepted.
        3xx (Redirects): Further action needs to be taken in order to complete the request.
        4xx (Client errors)The request contains bad syntax or cannot be fulfilled.
        5xx (Server errors): The server failed to fulfill an apparently valid request.
        """
        if code not in (self.standard_http_codes and [420, 451]):
            return await ctx.send(self.not_found_message)
        await ctx.send(f"https://random-d.uk/api/http/{code}.jpg")
