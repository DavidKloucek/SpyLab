import {
    List,
    useModal,
    useTable,
} from "@refinedev/antd";
import { LogicalFilter, useCustomMutation } from "@refinedev/core";
import { Badge, Modal, Space, Switch, Table, Tooltip } from "antd";
import { FaceBox, FacePicker } from "../../components/FacePicker";
import { useEffect, useState } from "react";
import { FaceSearchPanel } from "../../components/FaceSearchPanel";
import { FaceSimilarItemResponse } from "../../api/generated";

export const FaceFinderList = () => {

    const { tableProps, filters, setFilters } = useTable({
        syncWithLocation: false,
        queryOptions: { enabled: false },
        pagination: {
            pageSize: 50,
            mode: "client"
        }
    });

    const [selectedImage, setSelectedImage] = useState<File | null>(null);
    const [selectedBox, setSelectedBox] = useState<FaceBox | null>(null);
    const [showDetails, setShowDetails] = useState<FaceSimilarItemResponse | null>(null)

    const modal = useModal();

    useEffect(() => {
        if (showDetails && !modal.modalProps.open) {
            setShowDetails(null)
        }
    }, [modal, showDetails])

    const [similarList, setSimilarList] = useState<FaceSimilarItemResponse[]>([])
    const { mutateAsync, ...mutation } = useCustomMutation<FaceSimilarItemResponse[]>();

    useEffect(() => {
        const call = async () => {
            if (selectedBox && selectedImage) {
                const reqFilters = new Map()
                for (const filter of filters) {
                    if ("field" in filter) {
                        reqFilters.set(filter.field, filter.value)
                    }
                }
                const m = await mutateAsync({
                    url: "/api/similar-to-image",
                    method: "post",
                    config: {
                        headers: { "Content-Type": "multipart/form-data" }
                    },
                    values: {
                        x: selectedBox?.x,
                        y: selectedBox?.y,
                        w: selectedBox?.w,
                        h: selectedBox?.h,
                        image: selectedImage,
                    ...Object.fromEntries(reqFilters)
                    }
                });
                setSimilarList(m.data)
            }
        }
        call()
    }, [selectedBox, selectedImage, filters, mutateAsync])

    return <>
        <Modal
            {...modal.modalProps}
            width={800}
            title={
                showDetails
                    ? "Full size: " + showDetails.w + "×" + showDetails.h + "px"
                    : ""
            }
        >
            {showDetails && (
                <>
                    <FacePicker
                        faceBoxList={[{
                            x: showDetails.x,
                            y: showDetails.y,
                            w: showDetails.w,
                            h: showDetails.h,
                        }]}
                        imageUrl={showDetails.source_url}
                    />
                </>
            )}
        </Modal >
        <FaceSearchPanel
            onSelectedImage={(x) => {
                setSelectedBox(null)
                setSimilarList([])
                setSelectedImage(x.selectedImage)
            }}
            onSelectedFaceBox={(x) => {
                setSelectedBox(x)
            }}
        />
        <List title={<>Similar faces</>}>
            <Space align="start">
                <div style={{ float: "right" }}>
                    <Switch
                        checked={filters.find(x => x.value == 1)?.value}
                        onChange={(checked) => {
                            setFilters([
                                {
                                    field: "quality",
                                    operator: "eq",
                                    value: checked ? 1 : null,
                                } satisfies LogicalFilter,
                            ],
                                "replace");
                        }}
                        style={{ marginLeft: 8 }}
                    />
                    <span style={{ marginLeft: 8 }}>High quality</span>
                </div>
            </Space>
            <Table
                {...tableProps}
                dataSource={similarList}
                rowKey="id"
                loading={mutation.mutation.isPending}
            >
                <Table.Column dataIndex="fn" title={"Filename"} />
                <Table.Column
                    dataIndex="distance"
                    align="center"
                    title={<>Similarity distance</>}
                    render={(value) => (
                        <Tooltip title={value}>
                            <strong>{Math.round(Number(value) * 1000) / 1000}</strong>
                        </Tooltip>
                    )}
                />
                <Table.Column
                    dataIndex="quality"
                    title={"Image quality"}
                    align="center"
                    render={(value) => (
                        value > 0
                            ? <Badge count={Math.round(value)} style={{ backgroundColor: '#52c41a' }} />
                            : <Badge showZero count={Math.round(value)} />
                    )}
                />
                <Table.Column
                    dataIndex="confidence"
                    align="center"
                    title={"Is a face"}
                    render={(value) => {
                        return value + "%"
                    }}
                />
                <Table.Column
                    dataIndex="size"
                    align="center"
                    title={"Region size"}
                    render={(value, row: FaceSimilarItemResponse) => {
                        return row.w + "×" + row.h
                    }}
                />
                <Table.Column
                    dataIndex={"model"}
                    title={"Model"}
                    render={(value) => {
                        return value
                    }}
                />
                <Table.Column
                    dataIndex={"preview_url"}
                    title={"Preview"}
                    render={(value, row: FaceSimilarItemResponse) => {
                        return <img
                            loading="lazy"
                            src={value}
                            style={{ maxHeight: '100px', maxWidth: '100px' }}
                            onClick={() => {
                                modal.show()
                                setShowDetails(row)
                            }}
                        />
                    }}
                />
            </Table>
        </List>
    </>
};
