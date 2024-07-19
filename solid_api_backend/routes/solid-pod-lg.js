require('dotenv').config()

const querystring = require('querystring');
const {
    getSessionFromStorage,
    getSessionIdFromStorageAll,
    Session
  } = require("@inrupt/solid-client-authn-node");

const {
    addUrl,
    addStringNoLocale,
    createSolidDataset,
    createThing,
    getBoolean,
    getContentType,
    getInteger,
    getPodUrlAll,
    getSolidDataset,
    getThing,
    getThingAll,
    getStringNoLocale,
    isContainer,
    removeThing,
    saveSolidDatasetAt,
    setThing
  } = require("@inrupt/solid-client")

const { SCHEMA_INRUPT, RDF, AS, POSIX, LDP} = require( "@inrupt/vocab-common-rdf")

const express = require('express');
const router = express.Router();
const PORT = process.env.PORT || 3030;
const PORT_DJANGO = process.env.PORT_DJANGO || 8000;
const HOST = process.env.HOST || 'localhost';
const fetch = require("node-fetch");
// Authenticate (Node.js: Single-User App)


router.get("/login", async (req, res, next) => {
    // 1. Create a new Session
    console.log('user')
    const session = new Session({ keepAlive: false }); // Turn off periodic refresh of the Session in background
    req.session.sessionId = session.info.sessionId
    const CLIENTNAME = process.env.CLIENTNAME;
    const oidcIssuer =  req.query.issuer_url || 'https://solid.insightdatalg.ca/'
    console.log('oidcIssuer: ' + oidcIssuer)
    async function redirectToSolidIdentityProvider(url) {
      // Since we use Express in this example, we can call `res.redirect` to send the user to the
      // given URL, but the specific method of redirection depend on your app's particular setup.
      // For example, if you are writing a command line app, this might simply display a prompt for
      // the user to visit the given URL in their browser.
        res.redirect(url);
    }
    // 2. Start the login process; redirect handler will handle sending the user to their
    //    Solid Identity Provider.
    await session.login({
      // After login, the Solid Identity Provider will send the user back to the following
      // URL, with the data necessary to complete the authentication process
      // appended as query parameters:
      redirectUrl: `${HOST}:${PORT}/solid-pod-lg/callback`,
      oidcIssuer: oidcIssuer,
      // Pick an application name that will be shown when asked
      // to approve the application's access to the requested data.
      clientName: CLIENTNAME,
      
      handleRedirect: redirectToSolidIdentityProvider,
    });
  });


router.get("/callback", async (req, res) => {
    // 3. If the user is sent back to the `redirectUrl` provided in step 2,
    //    it means that the login has been initiated and can be completed. In
    //    particular, initiating the login stores the session in storage, 
    //    which means it can be retrieved as follows.
    console.log('callback')
    console.log('req.session.sessionId: ' + req.session.sessionId)
    const session = await getSessionFromStorage(req.session.sessionId);
    // 4. With your session back from storage, you are now able to
    //    complete the login process using the data appended to it as query
    //    parameters in req.url by the Solid Identity Provider:
    await session.handleIncomingRedirect(`${HOST}:${PORT}/solid-pod-lg${req.url}`)

    const session_info = querystring.stringify(session.info)

    const SolidPodLGurl = `${HOST}:${PORT_DJANGO}/pod-node/login-callback/`
    const login_callback_url = SolidPodLGurl + '?' + session_info

    res.redirect(login_callback_url);

    // if (session.info.isLoggedIn) {
    //
    //   return res.send(`<p>Logged in with the WebID ${session.info.webId}.</p>`)
    // }
});

  // 6. Once you are logged in, you can retrieve the session from storage,
  //    and perform authenticated fetches.
router.get("/fetch", async (req, res, next) => {
    console.log('fetch')
    const session = await getSessionFromStorage(req.query.sessionId);
    if(typeof session === "undefined") {
        res.status(500)
        return res.send('No session found. Please, log in to your pod provider again.')
        // return res.send(JSON.stringify({ error: 'No session found. Please, log in to your pod provider again.'}));
    }
    if(typeof req.query.resource === "undefined") {
        res.status(500)
        return res.send('Please pass the (encoded) URL of the Resource you want to fetch using `?resource=&lt;resource URL&gt;`.')
        // return res.send(JSON.stringify({ error: 'Please pass the (encoded) URL of the Resource you want to fetch using `?resource=&lt;resource URL&gt;`.'}));
    }
    const resourceURL = req.query.resource

    try {
        resp = await session.fetch(resourceURL)

    } catch(e) {
        res.status(500)
        return res.send(`An error occurred getting - ${resourceURL} -. Please, double check the url.`)
    }

    res.status(resp.status)
    const content_type  = resp.headers.get("content-type")
    if (content_type === 'text/turtle') {
        res.type(content_type)
        // resource_content = await resp.text()
        return res.send(await resp.text())
    } else {
        resource_content = ""
        if (resp.status === 200) {  // only ttl file here
            res.status(400)
            return res.send(`Invalid file type ${content_type}: not a ttl file.`)
        }
    }

    //

    // try {
    //     resource_content = await (await session.fetch(resourceURL)).text()
    //     const myDataset = await getSolidDataset(
    //         resourceURL,
    //         { fetch: fetch }  // fetch function from authenticated session
    //       );
    //     var folder_content = {};
    //     let items = getThingAll(myDataset);
    //     items.forEach((item, index) => {
    //         folder_content[index] = {
    //             url: item.url,
    //             isContainer: isContainer(item.url),
    //             size: getInteger(item, POSIX.size)
    //         }
    //         console.log('url:' + item.url)
    //         console.log('size:' + getInteger(item, POSIX.size))
    //         console.log('isContainer: ' + isContainer(item.url))
    //     });
    // } catch(e) {
    //     res.status(500)
    //     return res.send(JSON.stringify({ error: `An error occurred getting - ${resourceURL} -. Please, double check the url.`}));
    // }
    // return res.send(JSON.stringify({ resource_content: resource_content}));  // , folder_content: folder_content
});

// 7. To log out a session, just retrieve the session from storage, and
//    call the .logout method.
router.get("/logout", async (req, res, next) => {
    console.log('logout')
    console.log('req.query.sessionId:' + req.query.sessionId)
    const session = await getSessionFromStorage(req.query.sessionId);
    if(typeof session === "undefined") {
        res.setHeader('Content-Type', 'application/json');
        res.status(500)
        return res.send(JSON.stringify({ error: 'No session found. You are disconnected.'}));
    }
    session.logout();
    res.status(200)
    return res.end();
});

// 8. On the server side, you can also list all registered sessions using the
//    getSessionIdFromStorageAll function.
router.get("/sessions", async (req, res, next) => {
    console.log('sessions')
    console.log('req.session.sessionId: ' + req.session.sessionId)
    const sessionIds = await getSessionIdFromStorageAll();
    sessionIds.forEach(function (item, index) {
      console.log('sessionId ' + index + ' : ' + item);
    });
    return res.send(
        `<p>There are currently [${sessionIds.length}] visitors.</p>`
    );
    });

router.get("/download", async (req, res, next) => {
    console.log('download')
    const session = await getSessionFromStorage(req.query.sessionId);
    if(typeof session === "undefined") {
        res.status(500)
        return res.send('No session found. Please, log in to your pod provider again.')
        // return res.send(JSON.stringify({ error: 'No session found. Please, log in to your pod provider again.'}));
    }
    if(typeof req.query.resource === "undefined") {
        res.status(500)
        return res.send('Please pass the (encoded) URL of the Resource you want to fetch using `?resource=&lt;resource URL&gt;`.')
        // return res.send(JSON.stringify({ error: 'Please pass the (encoded) URL of the Resource you want to fetch using `?resource=&lt;resource URL&gt;`.'}));
    }
    const resourceURL = req.query.resource
    });


    
router.get("/test", async (req, res, next) => {
    console.log('test')
    res.setHeader('Content-Type', 'application/json');
    const session = await getSessionFromStorage(req.query.sessionId);
    if(typeof session === "undefined") {
        res.status(500)
        return res.send(JSON.stringify({ error: 'No session found. Please, log in to your pod provider again.'}));
    }
    if(typeof req.query.resource === "undefined") {
        res.status(500)
        return res.send(JSON.stringify({ error: 'Please pass the (encoded) URL of the Resource you want to fetch using `?resource=&lt;resource URL&gt;`.'}));
    }
    const resourceURL = req.query.resource

    const myDataset = await getSolidDataset(
        resourceURL,
        { fetch: fetch }  // fetch function from authenticated session
      );

    let items = getThingAll(myDataset);
    items.forEach((item) => {
        const i = getInteger(item, POSIX.size);
        console.log(item.url)
        console.log(i)
        console.log(isContainer(item.url))
    });
    // const containers = getThing(myDataset, LDP.Container)
    // console.log(containers)
    // containers.forEach((container) => {
    //     console.log(container)
    // });
    // let g= myDataset.graphs

    // console.log(await (await session.fetch(resourceURL)).text());
    resource_content = await (await session.fetch(resourceURL)).text()
    res.status(200)
    return res.send(JSON.stringify({ resource_content: resource_content}));
  });

module.exports = router;
