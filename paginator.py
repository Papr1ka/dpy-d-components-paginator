from typing import Any, Coroutine, Union
from discord_components import (
    DiscordComponents,
    Button,
    ButtonStyle,
    Interaction,
    ActionRow
)
from typing import List
from discord import Embed, Message
from asyncio import as_completed
from asyncio import TimeoutError as AsyncioTimeoutError
from discord.errors import NotFound


class Paginator():
    def __init__(
        self,
        client: DiscordComponents,
        send_func: Coroutine,
        contents: List[Embed],
        author_id: Any,
        timeout: Union[int, None]=None
            ) -> None:
        """Пагинатор Эмбедов на кнопках

        Args:
            client (DiscordComponents): ваш клиент
            send_func (Coroutine): корутина отправки сообщения
            (channel.send | ctx.send | другое)
            contents (List[Embed]): Список включённых в пагинатор эмбедов
            author_id (Any): идентификатор для проверки,
            что именно вы нажали на кнопку
            timeout (Union[int, None], optional):
            через какое время после последнего взаимодействия
            прекратить обслуживание Defaults to None
        """
        self.__client = client
        self.__send = send_func
        self.__contents = contents
        self.__index = 0
        self.__timeout = timeout
        self.__length = len(contents)
        self.__author_id = author_id
        self.check = lambda i: i.user.id == self.__author_id

    def get_components(self) -> ActionRow:
        return ActionRow([
            Button(style=ButtonStyle.blue, emoji="◀️", custom_id="l"),
            Button(
                label=f"Страница {self.__index + 1}/{self.__length}",
                disabled=True,
                custom_id="c"),
            Button(style=ButtonStyle.blue, emoji="▶️", custom_id="r")
        ])

    async def send(self) -> Message:
        aws = [
            self.__send(
                embed=self.__contents[self.__index],
                components=self.get_components()
            ),
            self.__pagi_loop(),
        ]
        for coro in as_completed(aws):
            r = await coro
            if r is not None:
                return r

    async def __pagi_loop(self) -> None:
        while True:
            try:
                interaction = await self.__client.wait_for(
                    "button_click",
                    timeout=self.__timeout
                )
            except AsyncioTimeoutError:
                return
            else:
                if self.check(interaction):
                    if interaction.custom_id == "l":
                        self.__index = (self.__index - 1) % self.__length
                    elif interaction.custom_id == "r":
                        self.__index = (self.__index + 1) % self.__length
                    await self.__button_callback(interaction)

    async def __button_callback(self, inter: Interaction, retr=1):
        try:
            await inter.respond(
                type=7,
                embed=self.__contents[self.__index],
                components=self.get_components()
            )
        except NotFound:
            if retr >= 1:
                await self.__button_callback(inter, retr=retr-1)
