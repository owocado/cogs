from typing import Any

from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

from .converter import ImageFinder, find_images_in_replies, search_for_images
from .utils import vision_ocr as do_vision_ocr


class OCR(commands.Cog):
    """Detect text in images using ocr.space or Google Cloud Vision API."""

    __authors__ = ["<@306810730055729152>", "TrustyJAID"]
    __version__ = "2.1.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  v{self.__version__}"
        )

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete"""
        pass


    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(read_message_history=True)
    @commands.command()
    async def ocr(
        self,
        ctx: commands.Context,
        detect_handwriting: bool | None = False,
        image: ImageFinder = None,
    ) -> None:
        """Detect text in an image through Google OCR API.

        You may use it to run OCR on old messages which contains attachments/image links.
        Simply reply to the said message with `[p]ocr` for detection to work.

        Pass `detect_handwriting` as True or `1` with command to more accurately detect handwriting from target image.

        **Example:**
        - `[p]ocr image/attachment/URL`
        - # To better detect handwriting in target image do:
        - `[p]ocr 1 image/attachment/URL`
        """
        async with ctx.typing():
            if not image:
                if ctx.message.reference and (message := ctx.message.reference.resolved):
                    image = await find_images_in_replies(message)  # type: ignore
                else:
                    image = await search_for_images(ctx)  # type: ignore
                if not image:
                    await ctx.send("No images or direct image links were detected. 😢")
                    return
            assert isinstance(image, list)
            resp = await do_vision_ocr(ctx, detect_handwriting, image=image[0])
            if not resp:
                return
            await ctx.send_interactive(
                pagify(resp.text_value, page_length=1984), box_lang="", timeout=120,
            )
            return

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(read_message_history=True)
    @commands.command()
    async def ocrtr(
        self,
        ctx: commands.Context,
        detect_handwriting: bool | None = False,
        image: ImageFinder = None,
    ) -> None:
        if not image:
            if ctx.message.reference and (message := ctx.message.reference.resolved):
                image = await find_images_in_replies(message)  # type: ignore
            else:
                image = await search_for_images(ctx)  # type: ignore
            if not image:
                await ctx.send("No images or direct image links were detected. 😢")
                return
        async with ctx.typing():
            assert isinstance(image, list)
            resp = await do_vision_ocr(ctx, detect_handwriting, image=image[0])
            if not resp:
                return

            from translate.models import DetectedLanguage
            from translate.translate import Translate
            cog = ctx.bot.get_cog('Translate')
            if not cog:
                await ctx.send('Translate function failed :pensive:')
                return
            assert isinstance(cog, Translate)

            text = resp.text_value or ""
            try:
                detected_lang = await cog._tr.detect_language(text, guild=ctx.guild)
            except Exception:
                # await ctx.send(str(exc))
                detected_lang = DetectedLanguage("auto", False, 0.0)
                from_lang = resp.fullTextAnnotation.language_code
            else:
                from_lang = detected_lang.language
            translated_text = await cog.run_translate(ctx, from_lang, "en", text)
            if not translated_text:
                await ctx.send_interactive(pagify(text, page_length=1984), box_lang="", timeout=120)
                await ctx.send("<a:_:947438639728689162> failed to translate funny")
                return
            content, embed = translated_text.embed(
                ctx.author, from_lang, "en", ctx.author, detected_lang.confidence
            )
            ref = ctx.message.to_reference(fail_if_not_exists=False)
            await ctx.send(embed=embed, reference=ref, mention_author=False)
            return

