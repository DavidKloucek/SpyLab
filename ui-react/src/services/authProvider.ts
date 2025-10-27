import type { AuthProvider } from "@refinedev/core";
import axiosClient, { getAccessToken, setAccessToken } from "./apiClient";

//export const TOKEN_KEY = "refine-auth";

type LoggedUser = {
    id: string;
    email: string;
    roles: string[];
}

const loggedUser = {
    data: null as null|string,
    set: (user: LoggedUser|null) => {
        loggedUser.data = user === null ? null : JSON.stringify(user)
        //localStorage.setItem("user", JSON.stringify(user));
    },
    get: (): LoggedUser | null => {
        //const u = localStorage.getItem("user")
        const u = loggedUser.data
        if (u !== null) {
            return JSON.parse(u) as LoggedUser;
        }
        return null;
    },
}

export const authProvider: AuthProvider = {
    
    login: async ({ email, password }) => {

        const req = await axiosClient.post("/api/login", {
            email,
            password
        }, {
            withCredentials: true
        })

        setAccessToken({
            token: req.data.token,    
            exp: Math.floor(Date.now() / 1000) + req.data.expires_in
        });

        const meReq = await axiosClient.get("/api/me", {
            withCredentials: true
        })
        const me = meReq.data;
        
        loggedUser.set(me as LoggedUser)
        return {
            success: true,
            redirectTo: "/",
        }

        return {
            success: false,
            error: {
                name: "LoginError",
                message: "Invalid username or password",
            },
        };
    },
    logout: async () => {
        loggedUser.data = null
        return {
            success: true,
            redirectTo: "/login",
        };
    },
    check: async () => {
        const token = loggedUser.get()
        if (token) {
            return {
                authenticated: true,
            };
        }

        return {
            authenticated: false,
            redirectTo: "/login",
        };
    },
    getPermissions: async () => null,
    getIdentity: async () => {
        const token = loggedUser.get()
        if (token) {
            return {
                id: token.id,
                name: token.email,
            };
        }
        return null;
    },
    onError: async (error) => {
        console.error(error);
        return { error };
    },
};
