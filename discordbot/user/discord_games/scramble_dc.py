import asyncio

from discordbot.user.discord_games.minigame_dc import MinigameDisc
from discordbot.user.variables import TIMEOUT, WIN, LOSE
from discordbot.utils.emojis import ALPHABET, STOP, ARROW_LEFT_2
from minigames.scramble import Scramble


class ScrambleDisc(MinigameDisc):
    def __init__(self, session):
        super().__init__(session)
        self.scramble_game = Scramble()

    async def start(self):
        if self.session.message_extra is not None:
            await self.session.message_extra.delete()
            self.session.message_extra = None

        await self.session.message.edit(content=self.get_content())
        await self.session.message.add_reaction(STOP)
        await self.session.message.add_reaction(ARROW_LEFT_2)

        for c in self.scramble_game.scrambled_word:
            await self.session.message.add_reaction(ALPHABET[c])

        await self.wait_for_player()

    async def wait_for_player(self):
        while True:
            def check(r, u):
                for c, e in ALPHABET.items():
                    if e == r.emoji and c in self.scramble_game.scrambled_word:
                        return u.id == self.session.context.author.id and r.message.id == self.session.message.id
                return u.id == self.session.context.author.id \
                       and (r.emoji == STOP or r.emoji == ARROW_LEFT_2) \
                       and r.message.id == self.session.message.id

            try:
                reaction, user = await self.session.bot.wait_for("reaction_add", check=check, timeout=TIMEOUT)
                if reaction.emoji == STOP:
                    self.status = LOSE
                    break

                if reaction.emoji == ARROW_LEFT_2:
                    char = self.scramble_game.remove_last()
                    if char != "_":
                        await self.session.message.add_reaction(ALPHABET[char])
                    await self.session.message.remove_reaction(reaction.emoji, self.session.context.author)

                else:
                    for c, e in ALPHABET.items():
                        if e == reaction.emoji:
                            self.scramble_game.guess(c)
                            if c not in self.scramble_game.scrambled_word:
                                await self.session.message.clear_reaction(e)
                            else:
                                await self.session.message.remove_reaction(e, self.session.context.author)
                            break

                if self.scramble_game.has_won():
                    self.status = WIN
                    break

                await self.session.message.edit(content=self.get_content())

            except asyncio.TimeoutError:
                self.status = LOSE
                break

        await self.session.message.edit(content=self.get_content())
        await self.session.message.clear_reactions()
        if self.status == WIN:
            for v in self.session.stats_players.values():
                v["wins"] += 1
        else:
            for v in self.session.stats_players.values():
                v["losses"] += 1
        await self.session.pause()

    def get_content(self):
        current_word = self.scramble_game.current_word
        scrambled_word = self.scramble_game.scrambled_word
        word_ = ""
        for c in current_word:
            if c == "_":
                word_ += "__ "
            else:
                word_ += f"{c} "

        content = f"```Letters: {' '.join(scrambled_word)}\n" \
                  f"{''.join(word_)}```"
        if self.status == WIN:
            content += "```You have won the game!```"
        elif self.status == LOSE:
            content += f"```You have lost the game!\nThe word was: '{''.join(self.scramble_game.word)}'```"
        elif len(scrambled_word) == 0:
            content += "```Wrong word, try again!```"
        return content
