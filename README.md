# iceberg-not-ify

Fork of the original icebergify for people who are too cool to use Spotify. This isn't hosted anywhere because I can't really be arsed to put it on some kind of free hosting service, but it's here for people who want to run Flask locally.

Still ends up using the Spotify API to get popularity, as it seems to be the best way to do that. Was looking at using Discogs's API (and determining popularity by the total number of users having/wanting a release for all releases by an artist), but without an artist ID you would have to use the search API which is the one thing you can't use without authentication. MusicBrainz probably would have worked, but the number of user rating votes for an artist isn't really enough to get meaningful results out of. So ironically enough, I still had to create a Spotify account and now I don't get to tell people I don't have one…

It only needs an application registered (to use the client ID and secret) though, which can be provided by the SPOTIFY_CLIENT_ID and SPOTIFY_SECRET environment variables, so at least all the code relating to user authentication can be taken out. This isn't a very elegant hack/fork with much effort put into it, just rips out any no longer relevant code slaps a form on the opening page for entering name (normally from the Spotify account) and to upload a JSON file containing historical play data; also instead of needing the data/ directory it writes the iceberg as a data: URL instead, and there is now a hidden layer below the iceberg (no graphics, just red text on a black background) to show any artists that are not found on Spotify and hence have no popularity (for ultimate hipster points). The stuff in privacy.html is probably no longer accurate or relevant now that there's no Spotify user account to be accessed, but I didn't touch that because I'm not a lawyer and might not know what I'm doing.

JSON file format: Object/dictionary like this:

```json
{
	"Album Artist/Album/1-01 Title.ogg": {
		"artist": "Artist",
		"album": "Album",
		"title": "Title",
		"genre": "Genre",
		"year": 1990,
		"plays": [
			"2022-01-15T16:29:49.806560",
			"2022-04-05T17:01:49.484394",
			"2022-07-02T22:42:06.780939"
		]
	}
}
```

"song path" may be a full path, or without the user's music folder (e.g. /home/user/Music) in which case it is effectively a relative path from there. "plays" is mandatory (a list of ISO formatted timestamps for each time the song has been played in history), the rest are optional. For iceberg-not-ify purposes: If "artist" is not provided, will be assumed from the path (which is assumed to use an album artist/album folder structure), the others are not used.

Intended for use with something like the "Song Change" plugin for Audacious or similar, and a script called from there. Presumably most media players at least have something among the lines of "call an external command when a song finishes", if not, that's unfortunate.
