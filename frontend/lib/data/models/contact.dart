class Contact {
  final int id;
  final String name;
  final String upiId;
  final String? phone;

  Contact({
    required this.id,
    required this.name,
    required this.upiId,
    this.phone,
  });

  factory Contact.fromJson(Map<String, dynamic> json) => Contact(
        id: json['id'] as int,
        name: json['name'] as String,
        upiId: json['upi_id'] as String,
        phone: json['phone'] as String?,
      );
}

class ContactCreateRequest {
  final String name;
  final String upiId;
  final String? phone;

  ContactCreateRequest({
    required this.name,
    required this.upiId,
    this.phone,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'upi_id': upiId,
        if (phone != null) 'phone': phone,
      };
}
