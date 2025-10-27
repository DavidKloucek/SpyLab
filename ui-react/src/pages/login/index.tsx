import { AuthPage } from "@refinedev/antd";

export const Login = () => {
    return (
        <AuthPage
            type="login"
            rememberMe={false}
            registerLink={false}
            forgotPasswordLink={false}
            formProps={{
                initialValues: { email: "root@root.cz", password: "root" },
            }}
        />
    );
};
