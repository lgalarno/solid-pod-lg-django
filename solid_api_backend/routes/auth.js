require('dotenv').config()

const querystring = require('querystring');
const {
    getSessionFromStorage,
    Session
  } = require("@inrupt/solid-client-authn-node");

const express = require('express');
const router = express.Router();
const HOST = process.env.HOST || 'localhost:';
const PORT = process.env.PORT || 3030;
const HTTP_PORT = process.env.HTTP_PORT || 3030;
const PORT_DJANGO = process.env.PORT_DJANGO || 8000;



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
    
    // console.log(await (await session.fetch(resourceURL)).text());
    try {
      await session.login({
        // After login, the Solid Identity Provider will send the user back to the following
        // URL, with the data necessary to complete the authentication process
        // appended as query parameters:
        redirectUrl: `${HOST}${HTTP_PORT}/api/auth/callback`,
        oidcIssuer: oidcIssuer,
        // Pick an application name that will be shown when asked
        // to approve the application's access to the requested data.
        clientName: CLIENTNAME,
        handleRedirect: redirectToSolidIdentityProvider,
      });
    } catch(err) {
        
        console.log('error: ' + err)
        console.log('error: ' + err.code )
        if (err.code === 'ENOTFOUND') {
          var mess ={error: `${oidcIssuer} not found. Please, double check the url.`}
        } else {
          var mess = err
        }
        return res.status(500).send(mess)
    } 
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
    console.log(typeof session)
    await session.handleIncomingRedirect(`${HOST}${HTTP_PORT}/api/auth${req.url}`)

    const session_info = querystring.stringify(session.info)
    console.log('sessionId: ' + session.info.sessionId)
    console.log('webID: ' + session.info.webId)
    console.log('isLoggedIn: ' + session.info.isLoggedIn)
    const SolidPodLGurl = `${HOST}${PORT_DJANGO}/pod-node/login-callback/`
    const login_callback_url = SolidPodLGurl + '?' + session_info

    res.redirect(login_callback_url);
});


router.post("/logout", async (req, res, next) => {
    console.log('logout')
    // console.log('req.query.sessionId:' + req.query.sessionId)
    console.log('sessionId: ' + req.body.sessionId)
    const session = await getSessionFromStorage(req.body.sessionId);
    res.setHeader('Content-Type', 'application/json');
    if(typeof session === "undefined") {
        res.status(500)
        json_data = JSON.stringify({ text: 'No session found. You are disconnected.'})
        // return res.send();
    } else {
      session.logout();
      res.status(200)
      json_data = JSON.stringify({ text: 'You have been disconnected.'})
    }  

    return res.send(json_data);
});


router.post("/session", async (req, res, next) => {
  console.log('session')
  let obj = {} 
  console.log('sessionId: ' + req.body.sessionId)
  let session = await getSessionFromStorage(req.body.sessionId);
  if (typeof session === "undefined") {
    obj.sessionId = false
    obj.webId = false
    obj.isLoggedIn = false
  } else {
    obj.sessionId = session.sessionId
    obj.webId = session.webId
    obj.isLoggedIn = session.isLoggedIn
  } 
  return res.send(obj);
});


module.exports = router;
