# Kịch bản Thuyết trình Đồ án: Dự đoán Đỉnh tải trong Hệ thống Serverless

Dưới đây là kịch bản nói (speaker notes) chi tiết tương ứng với từng Slide trong file `presentation.pdf`. Lời thoại được thiết kế tự nhiên, có ngắt nghỉ rõ ràng.

---

## Slide 1: Tiêu đề (Title Slide)
**Thời lượng:** 30 giây
**Thao tác:** Giữ nguyên slide.

**Kịch bản:**
> "Kính chào quý thầy cô trong hội đồng và các bạn. Hôm nay em rất vinh dự được trình bày đồ án với đề tài: 'Dự đoán Đỉnh tải trong Hệ thống Serverless - Giảm thiểu Khởi động lạnh bằng Machine Learning (cụ thể là mô hình LSTM)'. Đề tài do em thực hiện dưới sự hướng dẫn của Tiến sĩ Huỳnh Văn Đăng. Mời quý thầy cô cùng theo dõi."

---

## Slide 2: Vấn đề - Khởi động lạnh (Cold Start)
**Thời lượng:** 1 phút
**Thao tác:** 
- [Click 1]: Hiện đặc điểm Serverless.
- [Click 2]: Hiện mục Tiết kiệm.
- [Click 3]: Hiện mục Thách thức.

**Kịch bản:**
> "Đầu tiên, hãy nhìn vào bản chất của Serverless, cụ thể là Knative. Lợi ích lớn nhất của nó là khả năng Scale-to-Zero - thu hẹp toàn bộ ứng dụng về 0 khi không có người dùng. [Click 1, 2] Điều này giúp tiết kiệm tối đa chi phí.
> 
> Tuy nhiên, [Click 3] lợi ích này đi kèm với một cái giá rất đắt: 'Khởi động lạnh' (Cold Start). Khi không có container nào đang chạy mà đột ngột có một request gửi tới, hệ thống phải mất từ 3 đến 5 giây để đánh thức và khởi tạo container mới (như hình minh họa bên phải). Sự chậm trễ này gây ra trải nghiệm cực kỳ tồi tệ cho người dùng."

---

## Slide 3: Hạn chế của giải pháp mặc định
**Thời lượng:** 1 phút
**Thao tác:** Lần lượt [Click] để hiện 4 bước của cơ chế Reactive, sau đó [Click] hiện dòng cảnh báo đỏ.

**Kịch bản:**
> "Tại sao hệ thống mặc định của Knative lại chậm như vậy? Đó là do bộ Autoscaler của nó (KPA) hoạt động theo cơ chế 'Phản ứng' - Reactive. 
> [Click] Khi lượng truy cập tăng vọt, [Click] hệ thống mới bắt đầu nhận ra, [Click] nhưng lúc này đã quá muộn! Các request bị dồn ứ lại ở Gateway. [Click] Hệ thống hốt hoảng mở rộng cấp tốc, gây ra tình trạng quá tải cục bộ, hay còn gọi là hiệu ứng Domino.
> 
> [Click hiện cảnh báo] Từ đó, em nhận ra một chân lý: Để giải quyết bài toán này, hệ thống không thể chỉ 'Ngồi chờ và Phản ứng' được nữa. Chúng ta cần phải 'Đón đầu' bằng dự đoán!"

---

## Slide 4: Giải pháp Đề xuất - Predictive Scheduling
**Thời lượng:** 1 phút
**Thao tác:** [Click] lần lượt từng gạch đầu dòng.

**Kịch bản:**
> "Giải pháp em đề xuất là Lập lịch Dự đoán (Predictive Scheduling) tích hợp Trí tuệ Nhân tạo.
> [Click] Khối óc của hệ thống là mô hình Mạng nơ-ron LSTM. [Click] LSTM đặc biệt xuất sắc trong việc phân tích dữ liệu chuỗi thời gian, giúp nhận diện chu kỳ và xu hướng của lưu lượng truy cập mạng.
> [Click] Nhờ sự dự báo này, hệ thống sẽ thực hiện chiến lược 'Pre-warming'. Tức là hệ thống sẽ âm thầm khởi động sẵn các Container từ 5 đến 10 giây trước khi cơn bão traffic thực sự ập tới. Khi người dùng truy cập, Container đã sẵn sàng phục vụ ngay lập tức."

---

## Slide 5: Cốt lõi AI - Tế bào LSTM
**Thời lượng:** 45 giây
**Thao tác:** Giữ slide cho hội đồng xem hình, sau đó [Click] hiện chú thích 3 Cổng chính.

**Kịch bản:**
> "Trên màn hình là kiến trúc bên trong của một tế bào LSTM mà em đã hiện thực. Khác với mạng nơ-ron truyền thống, [Click] LSTM sở hữu 3 cánh cổng thông minh: Cổng Quên, Cổng Vào và Cổng Ra.
> 
> Chức năng cốt lõi của chúng là quyết định xem hệ thống nên 'quên đi' những thông tin lưu lượng rác nào (như các đợt spike giả, tấn công DDOS nhẹ) và 'ghi nhớ' những xu hướng traffic thực sự quan trọng để đưa ra con số dự đoán $h_t$ mượt mà và chính xác nhất."

---

## Slide 6: Kiến trúc Tổng thể của Hệ thống
**Thời lượng:** 1 phút
**Thao tác:** Trình bày theo luồng vòng tròn của sơ đồ.

**Kịch bản:**
> "Đây là bức tranh toàn cảnh về mặt kiến trúc. Hệ thống là một vòng lặp khép kín:
> Đầu tiên, Prometheus thu thập dữ liệu (RPS) từ K8s và đẩy về cho LSTM Service. LSTM sẽ dự đoán tải trong tương lai. 
> Kế tiếp, linh hồn của hệ thống - 'Predictive Controller' (Khối màu xanh lá) - sẽ đứng ra lấy kết quả dự đoán này, xử lý làm mịn, và gửi lệnh Scale chuẩn xác xuống Kubernetes API. 
> Toàn bộ quá trình này được theo dõi trực quan bằng các đường nét đứt thông qua hệ thống Dashboard."

---

## Slide 7: Thuật toán Làm mịn (Smoothing Algorithm)
**Thời lượng:** 1 phút
**Thao tác:** Chỉ vào từng ràng buộc trên slide.

**Kịch bản:**
> "Một vấn đề nảy sinh trong thực tế là: AI đôi khi có thể dự báo nhảy vọt (từ 1 lên 100), nếu ta áp dụng mù quáng con số này cho Kubernetes, hệ thống sẽ bị treo (Thrashing).
> 
> Do đó, em đã thiết kế Thuật toán Làm mịn (Smoothing). Nó hoạt động như một lớp khiên bảo vệ với 2 quy tắc: Chặn Min-Max tuyệt đối, và Cửa sổ vận tốc quy định giới hạn tăng/giảm trong mỗi chu kỳ. Triết lý ở đây là: 'Mở rộng thì nhanh để kịp đáp ứng, Thu hẹp thì phải từ từ để đề phòng dư chấn traffic'."

---

## Slide 8: Kịch bản Đỉnh tải 3 Pha (3-Phase Spike)
**Thời lượng:** 30 giây
**Thao tác:** Chỉ vào đồ thị trên màn hình.

**Kịch bản:**
> "Để chứng minh hệ thống hoạt động, em đã xây dựng một kịch bản Load Test khắc nghiệt chia làm 3 pha chuẩn mực:
> Pha 1 - Ramp Up: Lượng traffic tăng dựng đứng.
> Pha 2 - Hold Peak: Traffic giữ nguyên ở đỉnh điểm, test khả năng duy trì.
> Pha 3 - Ramp Down: Người dùng rời đi đột ngột."

---

## Slide 9: Kết quả Thực nghiệm
**Thời lượng:** 1 phút 15 giây
**Thao tác:** [Click] lần lượt từng dòng của bảng để hiện các con số nổi bật.

**Kịch bản:**
> "Và đây là kết quả đối chiếu giữa Knative mặc định và mô hình LSTM của đề tài:
> [Click] Đầu tiên, ấn tượng nhất là tỷ lệ Khởi động lạnh. Knative trượt hoàn toàn (100%), trong khi hệ thống của chúng ta đã triệt tiêu hoàn toàn xuống 0%.
> [Click] Điều này giúp độ trễ giảm từ 3500ms xuống chỉ còn 120ms (tức là tốc độ phản hồi nhanh hơn gấp gần 29 lần).
> [Click] Tuy nhiên, không có gì là miễn phí. Để đạt được tốc độ này, chúng ta chấp nhận đánh đổi một lượng nhỏ tài nguyên (hiệu quả giảm xuống 92.5%) do duy trì các Pod chạy không (Pre-warm). 
> [Click kết luận] Đây là một sự đánh đổi hoàn toàn xứng đáng cho những hệ thống cần độ trễ thấp như Thương mại điện tử hay Fintech."

---

## Slide 10: Tổng kết & Hướng phát triển
**Thời lượng:** 45 giây
**Thao tác:** [Click] hiện hướng phát triển.

**Kịch bản:**
> "Tóm lại, đề tài đã giải quyết triệt để bài toán Cold-start của Serverless bằng cách áp dụng thành công AI vào vòng đời DevOps. Hệ thống hoạt động an toàn nhờ Controller độc lập.
> 
> [Click] Về hướng phát triển, trong tương lai em dự kiến thử nghiệm mô hình Transformer mạnh mẽ hơn và sử dụng bộ dữ liệu traffic thực tế từ các sàn E-commerce thay vì môi trường giả lập."
