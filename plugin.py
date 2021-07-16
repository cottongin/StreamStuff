###
# Copyright (c) 2021, cottongin
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import asyncio

import requests
from shazamio import Shazam

from supybot import callbacks
from supybot.commands import wrap
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('StreamStuff')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class StreamStuff(callbacks.Plugin):
    """idk things and stuff"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(StreamStuff, self)
        self.__parent.__init__(irc)

    def die(self):
        super().die()


    @staticmethod
    def _fetch_mp3(url: str):
        # this is really dumb
        # TODO >> return object in memory

        response = requests.get(url, stream=True, timeout=5)

        data = b''
        loops = 0

        for chunk in response.iter_content(1024*20):
            loops += 1
            if loops >= 5 or not chunk:
                break
            data += chunk

        if not data:
            return

        with open('stream.mp3', 'wb') as fd:
            fd.write(data)

        return

    @classmethod
    async def _parse_shazam(self):
        # this is also really dumb

        out = {}
        try:
            shazam = Shazam()
            out = await shazam.recognize_song('stream.mp3')
        except Exception as err:
            print(err)
            pass

        message = (
            "Sorry, I couldn't find a match for what's currently playing!"
        )
        match = out.get('track')
        if match:
            message = "🎵 Now Playing: {title} by {subtitle} | {url}".format(
                title=match.get('title', 'Unknown'),
                subtitle=match.get('subtitle', 'Unknown'),
                url=match.get('share', {}).get('href', 'via Shazam')
            )

        return match, message

    @wrap
    def nowplaying(self, irc, msg, args):
        """
        Identify what is playing on a stream via Shazam.
        """
        url = self.registryValue('streamURL', msg.channel)
        if not url:
            irc.error("No stream provided, please configure this plugin.")
            return

        irc.reply("One second, listening...", notice=True)

        # TODO >> return the object in memory instead of writing to file
        _ = self._fetch_mp3(url)

        _, reply = asyncio.run(self._parse_shazam())
        irc.reply(reply)
        return

Class = StreamStuff


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
