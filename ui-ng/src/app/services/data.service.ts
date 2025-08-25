import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../env';

export type TFACE_ID = number

export interface Face {
    id: TFACE_ID
    fn: string
    model: string
    confidence: number
    preview_path: string
    source_filepath: string
    x: number
    y: number
    w: number
    h: number
    preview_url: string
    source_url: string
}

export interface SimilarFace extends Face {
    distance: number
    is_same: boolean
}

export interface DetailData {
    data: Face
    faces: Face[]
}

export interface AnalyzeResponse {
    preview_url: string
    source_url: string
    boxes: {
        face_confidence: number
        x: number
        y: number
        w: number
        h: number
        similar_faces: number
    }[]
}

@Injectable({
    providedIn: 'root'
})
export class DataService {
    constructor(private http: HttpClient) { }

    findDetailById(id: number): Observable<DetailData> {
        return this.http.get<DetailData>(environment.apiUrl + '/detail', {
            params: { id: id.toString() },
        });
    }

    findSimilarToId(params: { id: number, model: string, metric: string }) {
        return this.http.get<SimilarFace[]>(environment.apiUrl + '/similar-to-id', {
            params,
            responseType: 'json',
        });
    }

    findSimilarToImage(file: File, x: number, y: number, w: number, h: number) {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('x', String(x))
        formData.append('y', String(y))
        formData.append('w', String(w))
        formData.append('h', String(h))
        return this.http.post<SimilarFace[]>(environment.apiUrl + '/similar-to-image', formData);
    }

    findAll(q: string) {
        return this.http.get<Face[]>(environment.apiUrl + '/list', {
            params: { search: q, limit: 100 },
        })
    }

    analyzeImage(file: File) {
        const formData = new FormData();
        formData.append('file', file);
        return this.http.post<AnalyzeResponse>(environment.apiUrl + '/analyze', formData);
    }
}
