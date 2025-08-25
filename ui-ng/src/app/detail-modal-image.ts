import { CommonModule } from '@angular/common';
import { Component, ElementRef, ViewChild, computed, signal, input, output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import {MatTooltipModule} from '@angular/material/tooltip';

export interface FaceBox {
    x: number
    y: number
    w: number
    h: number
    is_strong?: boolean
    color?: string
    tooltip?: string
}

export interface CalculatedFaceBox<T extends FaceBox> {
    data: T
    left: string
    top: string
    width: string
    height: string
}

@Component({
    selector: 'detail-modal-image',
    standalone: true,
    imports: [
        CommonModule,
        MatButtonModule,
        MatTooltipModule
    ],
    template: `
        <div class="image-container">
            <img #image [src]="sourceUrl()" (load)="onImageLoad()" class="image"/>
            @if (boxes().length > 0) {
                @for (box of boxes(); track box.data) {
                    <div
                        [ngClass]="{'highlight-box': true, 'highlight-box-curr': box.data.is_strong}"
                        [style.width]="box.width"
                        [style.height]="box.height"
                        [style.left]="box.left"
                        [style.top]="box.top"
                        [style.borderColor]="box.data.color ?? 'lightgreen'"
                        (click)="clickFace.emit(box.data)"
                        [matTooltip]="box.data.tooltip"
                    ></div>
                }
            }
        </div>
    `,
    styleUrls: ['./detail-modal-image.component.css'],
})
export class DetailModalImageComponent<T extends FaceBox> {

    sourceUrl = input.required<string>();
    itemData = input.required<T[]>();

    clickFace = output<T>();

    @ViewChild('image') imageRef!: ElementRef;

    imageLoaded = signal(false)

    boxes = computed<CalculatedFaceBox<T>[]>(() => {
        if (this.imageLoaded()) {

            if (!this.imageRef) return [];
            const img = this.imageRef.nativeElement;

            const scaleX = img.clientWidth / img.naturalWidth;
            const scaleY = img.clientHeight / img.naturalHeight;

            return this.itemData().map(item => ({
                "data": item,
                "left": `${item.x * scaleX}px`,
                "top": `${item.y * scaleY}px`,
                "width": `${item.w * scaleX}px`,
                "height": `${item.h * scaleY}px`,
            }))
        }
        return []
    })

    onImageLoad() {
        if (this.imageRef?.nativeElement.complete) {
            this.imageLoaded.set(true);
        }
    }
}
