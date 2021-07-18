A rather basic Limnoria plugin that attempts to identify whatever song is
playing on a (configurable) stream

### Usage

```bash
cd "/your/limnoria/plugin/directory/here"
git clone https://github.com/cottongin/StreamStuff.git
pip install -r requirements.txt
```

From IRC:
```
<you> load StreamStuff
<you> config channel #yourchannel supybot.plugins.StreamStuff.streamURL https://yourstreamurl.com
<you> nowplaying
<bot> 🎵 Now Playing: A Song by Some Artist | via Shazam
```

### Configuration
You can configure a number of different output options, either globally or per channel, using Limnoria's built-in configuration management.

```
<you> config channel #yourchannel supybot.plugins.