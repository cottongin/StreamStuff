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
import io
import tempfile
import sys, traceback

import time

import requests
from shazamio import Shazam

# https://github.com/Horrendus/streamscrobbler-python
from .streamscrobbler import get_server_info

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
        # this is (still) really dumb
        # TODO: handle unexpected content better in the request

        data = None

        with requests.Session() as conn:
            response = conn.get(url, stream=True, timeout=5)

            data = bytes()
            loops = 0

            for chunk in response.iter_content(1024*5):
                loops += 1
                if loops >= 25 or not chunk:
                    break
                data += chunk

        return data

    @classmethod
    async def _parse_shazam(self, stream_info=None, audio_segment=None):
        # this is also really dumb

        out = {}
        shazam = Shazam()
        if not audio_segment:
            # TODO: fix this so it honors fs permissions etc
            try:
                out = await shazam.recognize_song('stream.mp3')
            except Exception as err:
                print(f"[FILE method] {err}")
                traceback.print_exc(file=sys.stdout)
                pass
        else:
            try:
                # so we make a NamedTemporaryFile because on *NIX we don't
                # always get a path or link to a regular TemporaryFile
                with tempfile.NamedTemporaryFile() as fake_file:
                    # TODO: abstract this out into a AudioSegmentClass
                    fake_file.write(audio_segment)
                    out = await shazam.recognize_song(fake_file.name)
            except Exception as err:
                print(f"[FAKE method] {err}")
                traceback.print_exc(file=sys.stdout)
                pass


        append = ""
        if stream_info:
            metadata = stream_info.get('metadata')
            if metadata:
                append = " | {}".format(metadata.get('song', '???'))

        message = (
            f"Sorry, Shazam could not identify what is playing.{append}"
        )
        match = out.get('track')
        if match:
            message = "🎵 Now Playing: {title} by {subtitle} | {url}{append}"
            message = message.format(
                title=match.get('title', 'Unknown'),
                subtitle=match.get('subtitle', 'Unknown'),
                url=match.get('share', {}).get('href', 'via Shazam'),
                append=append,
            )

        return match, message

    @wrap
    def nowplaying(self, irc, msg, args):
        """
        Identify what is playing on a stream via Shazam.
        """
        url = self.registryValue('streamURL', msg.channel)
        if not url:
            return irc.error(
                "No stream provided, please configure this plugin."
            )

        if self.registryValue('announceListening', msg.channel):
            irc.reply(
                "One second, listening...", 
                notice=True,
                private=True,
            )

        audio = self._fetch_mp3(url)

        stream_info = get_server_info(url)

        match, reply = asyncio.run(
            self._parse_shazam(
                stream_info=stream_info,
                audio_segment=audio,
            )
        )
        if not match:
            # we do not have a match, how do we handle that?
            target = msg.channel or msg.nick
            if self.registryValue('mismatches.failSilently', msg.channel):
                if self.registryValue('mismatches.failToNotice', msg.channel):
                    return irc.reply(reply, notice=True, private=True)
            elif self.registryValue('mismatches.failToNotice', msg.channel):
                return irc.reply(reply, notice=True, private=True)
            else:
                # this might not strictly be necessary...
                return irc.reply(reply, to=target)
            return

        return irc.reply(reply)

Class = StreamStuff


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
