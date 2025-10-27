import { Authenticated, Refine } from "@refinedev/core";
import { DevtoolsPanel, DevtoolsProvider } from "@refinedev/devtools";
import { RefineKbar, RefineKbarProvider } from "@refinedev/kbar";

import {
    ErrorComponent,
    ThemedLayoutV2,
    ThemedSiderV2,
    useNotificationProvider,
} from "@refinedev/antd";
import "@refinedev/antd/dist/reset.css";

import routerBindings, {
    CatchAllNavigate,
    DocumentTitleHandler,
    NavigateToResource,
    UnsavedChangesNotifier,
} from "@refinedev/react-router";
import dataProvider from "@refinedev/simple-rest";
import { App as AntdApp } from "antd";
import { BrowserRouter, Outlet, Route, Routes } from "react-router";
import { Header } from "./components/header";
import { ColorModeContextProvider } from "./contexts/color-mode";
import { Login } from "./pages/login";
import { FaceFinderList } from "./pages/face-finder";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { UserList } from "./pages/user/list";
import { Home } from "./pages/dashboard/home";
import axiosClient, { resourceApiUrl } from "./services/apiClient";
import { authProvider } from "./services/authProvider";

function App() {
    const qp = new QueryClient()
    const dp = dataProvider(resourceApiUrl, axiosClient);

    return (
        <QueryClientProvider client={qp}>
            <BrowserRouter>
                <RefineKbarProvider>
                    <ColorModeContextProvider>
                        <AntdApp>
                            <DevtoolsProvider>
                                <Refine
                                    dataProvider={dp}
                                    notificationProvider={useNotificationProvider}
                                    routerProvider={routerBindings}
                                    authProvider={authProvider}
                                    resources={[
                                        {
                                            name: "face-finder",
                                            list: "/face-finder",
                                            meta: {
                                                canDelete: true,
                                            },
                                        },
                                        {
                                            name: "users",
                                            list: "/users",
                                            meta: {
                                                canDelete: false,
                                            },
                                        },
                                    ]}
                                    options={{
                                        syncWithLocation: true,
                                        warnWhenUnsavedChanges: true,
                                        useNewQueryKeys: true,
                                        projectId: "H3b24T-fOBw9I-1q9FqW", title: {
                                            icon: null,
                                            text: "SpyLab",
                                        },
                                    }}
                                >
                                    <Routes>
                                        <Route
                                            element={
                                                <Authenticated
                                                    key="authenticated-inner"
                                                    fallback={<CatchAllNavigate to="/login" />}
                                                >
                                                    <ThemedLayoutV2
                                                        Header={Header}
                                                        Sider={(props) => <ThemedSiderV2 {...props} fixed />}
                                                    >
                                                        <Outlet />
                                                    </ThemedLayoutV2>
                                                </Authenticated>
                                            }
                                        >
                                            <Route path="/">
                                                <Route index element={<Home />} />
                                            </Route>
                                            <Route path="/face-finder">
                                                <Route index element={<FaceFinderList />} />
                                            </Route>
                                            <Route path="/users">
                                                <Route index element={<UserList />} />
                                            </Route>
                                            <Route path="*" element={<ErrorComponent />} />
                                        </Route>
                                        <Route
                                            element={
                                                <Authenticated
                                                    key="authenticated-outer"
                                                    fallback={<Outlet />}
                                                >
                                                    <NavigateToResource />
                                                </Authenticated>
                                            }
                                        >
                                            <Route path="/login" element={<Login />} />
                                        </Route>
                                    </Routes>

                                    <RefineKbar />
                                    <UnsavedChangesNotifier />
                                    <DocumentTitleHandler />
                                </Refine>
                                <DevtoolsPanel />
                            </DevtoolsProvider>
                        </AntdApp>
                    </ColorModeContextProvider>
                </RefineKbarProvider>
            </BrowserRouter>
        </QueryClientProvider>
    );
}

export default App;
