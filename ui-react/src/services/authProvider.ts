import type { AuthProvider } from "@refinedev/core";
import axiosClient, { setAccessToken } from "./apiClient";

type LoggedUser = {
    id: string;
    email: string;
    roles: string[];
}

const loggedUser = {
    data: null as null | string,
    set: (user: LoggedUser | null) => {
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
        try {
            const req = await axiosClient.post("/api/login", {
                email,
                password
            }, {
                withCredentials: true
            });

            setAccessToken({
                token: req.data.token,
                exp: Math.floor(Date.now() / 1000) + req.data.expires_in
            });

            const meReq = await axiosClient.get("/api/me", {
                withCredentials: true
            });
            const me = meReq.data;

            loggedUser.set(me as LoggedUser);

            return {
                success: true,
                redirectTo: "/",
            };
        } catch (err) {
            const error = err as any;
            const message = error?.response?.data?.message || error.message || "Neznámá chyba";
            const status = error?.response?.data?.statusCode || error.statusCode || 500;

            return {
                success: false,
                error: {
                    name: "LoginError",
                    message: `${message} (status code: ${status})`,
                },
            };
        }
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
    getPermissions: async () => {
        return null
    },
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
        if (error.status === 401 || error.status === 403) {
            return {
                logout: true,
                redirectTo: "/login",
                error,
            };
        }
        return {};
    },
};
