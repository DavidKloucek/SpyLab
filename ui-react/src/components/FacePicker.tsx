'use client';

import { Tooltip } from 'antd';
import React from 'react';
import { useElementSize } from '../hooks';

export interface FaceBox {
    x: number;
    y: number;
    w: number;
    h: number;
    is_strong?: boolean;
    color?: string;
    tooltip?: string;
}

export interface CalculatedFaceBox<T extends FaceBox> {
    data: T;
    left: string;
    top: string;
    width: string;
    height: string;
}

interface DetailModalImageProps<T extends FaceBox> {
    imageUrl: string;
    faceBoxList: T[];
    onClickFace?: (box: T) => void;
}

export function FacePicker<T extends FaceBox>({
    imageUrl: sourceUrl,
    faceBoxList: itemData,
    onClickFace,
}: DetailModalImageProps<T>) {
    const [imageLoaded, setImageLoaded] = React.useState(false);
    const resize = useElementSize<HTMLImageElement>()

    const boxes = React.useMemo<CalculatedFaceBox<T>[]>(() => {
        if (!imageLoaded || !resize.ref) return [];

        const scaleX = (resize.clientWidth ?? 0) / (resize.naturalWidth ?? 0);
        const scaleY = (resize.clientHeight ?? 0) / (resize.naturalHeight ?? 0);

        return itemData.map((item) => ({
            data: item,
            left: `${item.x * scaleX}px`,
            top: `${item.y * scaleY}px`,
            width: `${item.w * scaleX}px`,
            height: `${item.h * scaleY}px`,
        }));
    }, [imageLoaded, itemData, resize]);
    
    const handleImageLoad = () => {
        if (resize.ref.current?.complete) {
            setImageLoaded(true);
        }
    };

    return (
        <div className="image-container" style={{ position: 'relative' }}>
            <img
                ref={resize.ref}
                src={sourceUrl}
                onLoad={handleImageLoad}
                className="image"
                style={{ width: 'auto', height: 'auto', display: 'block', maxHeight: '500px' }}
            />
            {boxes.map((box, index) => (
                <Tooltip key={index} title={box.data.tooltip || ''}>
                    <div
                        onClick={() => {
                            if (onClickFace) {
                                onClickFace(box.data)
                            }
                        }}
                        style={{
                            position: 'absolute',
                            left: box.left,
                            top: box.top,
                            width: box.width,
                            height: box.height,
                            border: `2px solid ${box.data.color ?? 'lightgreen'}`,
                            cursor: 'pointer',
                            boxSizing: 'border-box',
                        }}
                        className={`highlight-box ${box.data.is_strong ? 'highlight-box-curr' : ''}`}
                    ></div>
                </Tooltip>
            ))}
        </div>
    );
}
