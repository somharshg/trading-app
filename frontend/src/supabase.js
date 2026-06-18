import { initializeApp } from "firebase/app"
import { getAuth, GoogleAuthProvider } from "firebase/auth"
import { getFirestore } from "firebase/firestore"

const firebaseConfig = {
  apiKey: "AIzaSyDbMn64l4PcWB4K-26detbFFuCe1284hu0",
  authDomain: "trading-app-bfdff.firebaseapp.com",
  projectId: "trading-app-bfdff",
  storageBucket: "trading-app-bfdff.firebasestorage.app",
  messagingSenderId: "784980914425",
  appId: "1:784980914425:web:30dc13182bf7f2834cf228"
}

const app = initializeApp(firebaseConfig)

export const auth = getAuth(app)
export const provider = new GoogleAuthProvider()
export const db = getFirestore(app)