import 'package:equatable/equatable.dart';

class ProfileDetails extends Equatable {
  const ProfileDetails({
    required this.displayName,
    required this.email,
    required this.avatar,
    required this.status,
    required this.stats,
    required this.sessions,
  });

  final String displayName;
  final String email;
  final String avatar;
  final String status;
  final ProfileStats stats;
  final List<ProfileSession> sessions;

  @override
  List<Object?> get props => [displayName, email, avatar, status, stats, sessions];
}

class ProfileStats extends Equatable {
  const ProfileStats({
    required this.trackedBooks,
    required this.reviews,
    required this.eventsLogged,
    required this.recommendationMatch,
  });

  final int trackedBooks;
  final int reviews;
  final int eventsLogged;
  final String recommendationMatch;

  @override
  List<Object?> get props => [trackedBooks, reviews, eventsLogged, recommendationMatch];
}

class ProfileSession extends Equatable {
  const ProfileSession({
    required this.device,
    required this.location,
    required this.lastSeen,
    required this.current,
  });

  final String device;
  final String location;
  final String lastSeen;
  final bool current;

  @override
  List<Object?> get props => [device, location, lastSeen, current];
}
