from akinator.async_aki import Akinator

from discordbot.messagemanager import MessageManager
from discordbot.user.discord_games.minigame_dc import MinigameDisc
from discordbot.utils.emojis import ALPHABET, STOP, QUESTION


class AkinatorDiscord(MinigameDisc):
    def __init__(self, session):
        super().__init__(session)
        self.akinator = Akinator()
        self.guessed = False
        self.player = self.session.players[0]

    async def start_game(self):
        await self.akinator.start_game()
        await MessageManager.edit_message(self.message, self.get_content())

        await MessageManager.add_reaction_event(self.message, ALPHABET["y"], self.player.id, self.on_yes_reaction)
        await MessageManager.add_reaction_event(self.message, ALPHABET["n"], self.player.id, self.on_no_reaction)
        await MessageManager.add_reaction_event(self.message, QUESTION, self.player.id, self.on_dontknow_reaction)
        await MessageManager.add_reaction_event(self.message, STOP, self.player.id, self.on_stop_reaction)

        self.start_timer()

    async def on_yes_reaction(self):
        self.cancel_timer()

        await self.akinator.answer(0)
        await MessageManager.remove_reaction(self.message, ALPHABET["y"], self.player.member)
        await self.check_akinator_guess()

    async def on_no_reaction(self):
        self.cancel_timer()

        await self.akinator.answer(1)
        await MessageManager.remove_reaction(self.message, ALPHABET["n"], self.player.member)
        await self.check_akinator_guess()

    async def on_dontknow_reaction(self):
        self.cancel_timer()

        await self.akinator.answer(2)
        await MessageManager.remove_reaction(self.message, QUESTION, self.player.member)
        await self.check_akinator_guess()

    async def check_akinator_guess(self):
        await MessageManager.edit_message(self.session.message, self.get_content())
        if self.akinator.progression >= 80 or self.akinator.step == 80:
            await self.akinator.win()
            self.guessed = True
            await self.end_game()
        else:
            self.start_timer()

    async def on_player_timed_out(self):
        self.player.set_idle()
        await self.end_game()

    async def on_stop_reaction(self):
        self.cancel_timer()
        await self.end_game()

    def get_content(self):
        content = f"Question {int(self.akinator.step) + 1}: *{self.akinator.question}*\n"
        if self.guessed:
            content = f"Akinator guesses: {self.akinator.first_guess['name']}\n{self.akinator.first_guess['absolute_picture_path']}"
        return content
