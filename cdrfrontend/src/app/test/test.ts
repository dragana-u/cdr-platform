//todo remove when done integrating with backend
import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-test',
  imports: [],
  templateUrl: './test.html',
  styleUrl: './test.css',
})
export class Test implements OnInit {
  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get(`${environment.baseUrl}test`, { responseType: 'text' })
      .subscribe({
        next: (res) => console.log(res)
      });
  }
}
