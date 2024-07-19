require('dotenv').config()

const querystring = require('querystring');
const {
    getSessionFromStorage,
    getSessionIdFromStorageAll,
    Session
  } = require("@inrupt/solid-client-authn-node");



const { SCHEMA_INRUPT, RDF, AS, POSIX, LDP} = require( "@inrupt/vocab-common-rdf")

const express = require('express');
const router = express.Router();

// Authenticate (Node.js: Single-User App)


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


module.exports = router;
