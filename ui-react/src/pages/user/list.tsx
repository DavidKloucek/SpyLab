import {
    List,
    ShowButton,
    useTable,
} from "@refinedev/antd";
import { type BaseRecord } from "@refinedev/core";
import { Space, Table } from "antd";

export const UserList = () => {
    const { tableProps } = useTable({
        syncWithLocation: true,
        resource: "users"
    });

    return <>
        <List>
            <Table {...tableProps} rowKey="id">
                <Table.Column
                    dataIndex="id"
                    title={"ID"}
                />
                <Table.Column
                    dataIndex={"email"}
                    title={"Email"}
                />
                <Table.Column
                    title={"Actions"}
                    dataIndex="actions"
                    render={(_, record: BaseRecord) => (
                        <Space>
                            <ShowButton hideText size="small" recordItemId={record.id} />
                        </Space>
                    )}
                />
            </Table>
        </List>
    </>
};
