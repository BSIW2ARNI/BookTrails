class NfcException implements Exception {
  const NfcException(this.message, {this.code});

  final String message;
  final String? code;

  @override
  String toString() => message;
}
