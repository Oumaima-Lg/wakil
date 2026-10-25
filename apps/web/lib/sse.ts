export type EvenementSSE = { nom: string; donnees: unknown };

/**
 * Lit un flux SSE (text/event-stream) reçu par fetch, et rend les événements un par un, dès leur arrivée.
 *
 * EventSource, l'outil SSE du navigateur, ne sait faire que des GET ; /chat est un POST avec un corps JSON.
 * On lit donc le corps nous-mêmes. Un événement ressemble à :
 *   event: reponse
 *   data: {"texte": "Solde dyalek howa 2 350 DH."}
 *   (ligne vide)
 */
export async function* lireEvenements(corps: ReadableStream<Uint8Array>): AsyncGenerator<EvenementSSE> {
  const lecteur = corps.getReader();
  const decodeur = new TextDecoder(); // le réseau livre des octets : on les transforme en texte
  let tampon = "";
  while (true) {
    const { value, done } = await lecteur.read(); // attend le prochain morceau envoyé par le serveur
    if (done) return;
    // stream: true : si un caractère (« é », une lettre arabe) est coupé entre deux morceaux, on attend la suite
    tampon += decodeur.decode(value, { stream: true });
    // Un morceau peut contenir plusieurs événements, ou la moitié d'un seul : on ne traite que les blocs complets.
    let fin = tampon.indexOf("\n\n");
    while (fin !== -1) {
      const bloc = tampon.slice(0, fin);
      tampon = tampon.slice(fin + 2);
      let nom = "message";
      let data = "";
      for (const ligne of bloc.split("\n")) {
        if (ligne.startsWith("event:")) nom = ligne.slice(6).trim();
        else if (ligne.startsWith("data:")) data += ligne.slice(5).trim();
      }
      yield { nom, donnees: data ? JSON.parse(data) : null };
      fin = tampon.indexOf("\n\n");
    }
  }
}
